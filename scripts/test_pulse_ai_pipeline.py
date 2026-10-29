"""End-to-end offline mock respects real source/packet provenance, no paid AI."""
import unittest
from ai_research_packets import build_all,read_json
from pulse_ai_pipeline import MockAIProvider,OpenAIProvider,simulate
from pulse_ai_analysis_queue import build_queue,ROOT
from earnings_research_candidates import digest

class AIMockPipelineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packets=build_all()
  cls.registry=read_json(ROOT/"public/data/official-registry.json")
 def queue_for(self,ticker):
  packet=self.packets[ticker]
  facts=packet["financialObservations"]
  if not facts:raise unittest.SkipTest("Retained source packet lacks observations for offline fixture")
  item=facts[0]
  candidate={"id":"earnings-candidate:"+"f"*32,
   "companyId":packet["companyId"],"ticker":ticker,
   "sourceUrl":item["sourceUrl"],"sourceSha256":item["sourceSha256"],
   "reportPeriod":"Q3 2026","firstCandidateAt":"2026-10-29T00:00:00Z",
   "publicationStatus":"not-approved","aiAnalysisExecuted":False,
   "status":"needs-review","metrics":[{"id":item["observationId"]}]}
  candidate["payloadSha256"]=digest(candidate)
  data={"version":1,"candidates":[candidate],"latestByCompany":{candidate["companyId"]:candidate["id"]}}
  return build_queue(data,{},self.registry,"2026-10-29T01:00:00Z")
 def test_dlo_or_iren_mock_never_claims_model_or_approval(self):
  # DLO has retained live-source-shaped financial observations in the repo.
  queue=self.queue_for("DLO")
  result=simulate(queue,self.packets,"DLO","2026-10-29T02:00:00Z")
  self.assertEqual(result["stages"][-1],"mock-pending-review")
  self.assertFalse(result["paidAiExecuted"])
  self.assertEqual(result["analysisMode"],"mock-simulation-no-model")
  self.assertEqual(result["proposal"]["analysisMode"],"deterministic-no-ai")
  self.assertEqual(result["validation"]["modelChanges"],0)
  self.assertFalse(result["approvedModelChanged"])
  self.assertEqual(queue["jobs"][0]["status"],"queued")
 def test_invalid_version_is_rejected_before_simulation(self):
  queue=self.queue_for("DLO")
  queue["jobs"][0]["sourceSha256"]="1"*64
  with self.assertRaisesRegex(ValueError,"no financial observation"):
   simulate(queue,self.packets,"DLO","2026-10-29T02:00:00Z")
 def test_blocked_queue_and_no_paid_provider(self):
  queue=self.queue_for("DLO")
  queue["jobs"][0]["status"]="blocked"
  with self.assertRaisesRegex(ValueError,"blocked"):
   simulate(queue,self.packets,"DLO","2026-10-29T02:00:00Z")
  with self.assertRaisesRegex(RuntimeError,"disabled"):
   OpenAIProvider().analyze(self.packets["DLO"])
 def test_valid_mock_format_without_api(self):
  proposal=MockAIProvider().analyze(self.packets["DLO"])
  self.assertEqual(proposal["suggestedScenarioReview"],[])
  self.assertEqual(proposal["proposedValuationAction"],"no-automatic-change")
  self.assertTrue(proposal["analystQuestions"])
 def test_meta_if_retained_source_available(self):
  if not self.packets["META"]["financialObservations"]:
   self.skipTest("Live META observation is tested by PR intake after source retrieval")
  queue=self.queue_for("META")
  result=simulate(queue,self.packets,"META","2026-10-29T02:00:00Z")
  self.assertEqual(result["ticker"],"META")

if __name__=="__main__":unittest.main()
