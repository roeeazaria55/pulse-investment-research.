"""Simulate a complete budget reservation and settlement; never call OpenAI."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pulse_ai_actions as actions
from ai_research_packets import build_all
from pulse_ai_analysis_queue import build_queue,validate,ROOT
from pulse_ai_cost_guard import record_call
from earnings_research_candidates import digest

NOW="2026-10-29T10:00:00Z"

class RemoteSpendTransactions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packet=build_all()["DLO"]
  cls.registry=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))
 def _queue(self):
  packet=self.packet
  item=packet["financialObservations"][0]
  c={"id":"earnings-candidate:"+"b"*32,"companyId":packet["companyId"],
     "ticker":"DLO","sourceUrl":item["sourceUrl"],"sourceSha256":item["sourceSha256"],
     "reportPeriod":"Q2 2026","firstCandidateAt":"2026-10-29T00:00:00Z",
     "publicationStatus":"not-approved","aiAnalysisExecuted":False,"status":"needs-review",
     "metrics":[{"id":item["observationId"]}]}
  c["payloadSha256"]=digest(c)
  return build_queue({"version":1,"latestByCompany":{c["companyId"]:c["id"]},"candidates":[c]},
                     {},self.registry,NOW)
 def test_reserve_persists_before_private_billed_review(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);state=root/"pulse-data";private=root/"private"
   state.mkdir();private.mkdir()
   q=self._queue()
   actions.atomic_write(state/actions.STATE_QUEUE,q)
   selected=q["jobs"][0]
   payload=json.dumps(self.packet,ensure_ascii=False,separators=(",",":"))
   with patch.object(actions,"load_context",return_value=(self.registry,q,{})), \
        patch.object(actions,"choose",return_value=(selected,self.packet,payload)):
    decision=actions.reserve_once(state,private,NOW,"gpt-6.1-sol")
   self.assertTrue(decision["ready"])
   after=json.loads((state/actions.STATE_QUEUE).read_text())
   self.assertEqual(after["jobs"][0]["status"],"processing")
   self.assertFalse(after["jobs"][0]["analysisExecuted"])
   self.assertEqual(after["jobs"][0]["attempts"],1)
   ledger=json.loads((state/actions.STATE_LEDGER).read_text())
   self.assertEqual(len(ledger["holds"]),1)
   with patch.object(actions,"load_context",return_value=(self.registry,after,{})), \
        patch.object(actions,"choose",return_value=(selected,self.packet,payload)):
    duplicate=actions.reserve_once(state,private,"2026-10-29T11:00:00Z","gpt-6.1-sol")
    self.assertFalse(duplicate["ready"])
    self.assertEqual(duplicate["reason"],"already-processed-or-reserved")
 def test_settlement_records_cost_and_only_unapproved_research(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);state=root/"pulse-data";private=root/"private"
   state.mkdir();private.mkdir()
   q=self._queue()
   actions.atomic_write(state/actions.STATE_QUEUE,q)
   selected=q["jobs"][0]
   payload=json.dumps(self.packet,ensure_ascii=False,separators=(",",":"))
   with patch.object(actions,"load_context",return_value=(self.registry,q,{})), \
        patch.object(actions,"choose",return_value=(selected,self.packet,payload)):
    actions.reserve_once(state,private,NOW,"gpt-6.1-sol")
   original=json.loads((state/actions.STATE_LEDGER).read_text())
   billed,receipt=record_call(original,"DLO",self.packet["contentSha256"],"gpt-6.1-sol",NOW,
       {"input_tokens":2000,"output_tokens":250,"input_tokens_details":{"cached_tokens":0}})
   actions.atomic_write(private/"ledger.json",billed)
   obs=self.packet["financialObservations"][0]["observationId"]
   proposal={"version":1,"companyId":self.packet["companyId"],
     "packetContentSha256":self.packet["contentSha256"],"status":"requires-human-review",
     "analysisMode":"model-generated-unverified",
     "evidenceCitations":[{"evidenceId":obs,"kind":"financial-observation",
                            "claim":"Source metric for review","uncertainty":"Pending reconciliation"}],
     "analystQuestions":["Is the reported metric comparable?"],"interpretations":[],
     "suggestedScenarioReview":[],"proposedValuationAction":"no-automatic-change"}
   actions.atomic_write(private/"review.json",proposal)
   changed=json.loads((state/actions.STATE_QUEUE).read_text())
   with patch.object(actions,"load_context",return_value=(self.registry,changed,{})), \
        patch.object(actions,"build_all",return_value={"DLO":self.packet}):
    result=actions.settle(state,private,"2026-10-29T11:00:00Z")
   self.assertTrue(result["draft"])
   self.assertFalse(result["autoApproval"])
   final=json.loads((state/actions.STATE_QUEUE).read_text())
   self.assertEqual(final["jobs"][0]["status"],"pending-review")
   self.assertTrue(final["jobs"][0]["analysisExecuted"])
   finalledger=json.loads((state/actions.STATE_LEDGER).read_text())
   self.assertEqual(len(finalledger["calls"]),1)
   self.assertFalse(finalledger["holds"])
   published=json.loads((state/actions.STATE_REVIEWS).read_text())
   self.assertEqual(published["drafts"][0]["publicationStatus"],"not-approved")
   self.assertIsNone(published["drafts"][0]["approvedTargetPrice"])
 def test_unbilled_failure_remains_reserved(self):
  with tempfile.TemporaryDirectory() as folder:
   state=Path(folder)/"data";private=Path(folder)/"private"
   state.mkdir();private.mkdir()
   q=self._queue();actions.atomic_write(state/actions.STATE_QUEUE,q)
   first=q["jobs"][0];payload=json.dumps(self.packet,ensure_ascii=False,separators=(",",":"))
   with patch.object(actions,"load_context",return_value=(self.registry,q,{})), \
        patch.object(actions,"choose",return_value=(first,self.packet,payload)):
    actions.reserve_once(state,private,NOW,"gpt-6.1-sol")
   changed=json.loads((state/actions.STATE_QUEUE).read_text())
   actions.atomic_write(private/"ledger.json",json.loads((state/actions.STATE_LEDGER).read_text()))
   with patch.object(actions,"load_context",return_value=(self.registry,changed,{})):
    with self.assertRaisesRegex(ValueError,"No recorded API usage"):
     actions.settle(state,private,"2026-10-29T11:00:00Z")
   self.assertEqual(json.loads((state/actions.STATE_QUEUE).read_text())["jobs"][0]["status"],"processing")

if __name__=="__main__":unittest.main()
