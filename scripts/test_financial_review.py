"""Review decisions never change financial research automatically."""
import copy
import unittest
from financial_review import apply_review

TIME="2026-10-22T13:00:00+00:00"
ROW={"id":"observation:abc", "companyId":"us-dlo-nasdaq-a","metricId":"revenue",
     "reviewVersionId":"review:abc","sourceSha256":"a"*64,
     "sourceUrl":"https://rss.globenewswire.com/news-release/dlocal",
     "sourceRaw":"399.7", "basis":"IFRS (rounded issuer KPI)", "unit":"USD million",
     "value":399.7, "periodStart":"2026-04-01","periodEnd":"2026-06-30",
     "reviewStatus":"pending-review","revisedSource":False}
REQUEST={"observationId":ROW["id"],"reviewVersionId":ROW["reviewVersionId"],
         "sourceSha256":ROW["sourceSha256"],"decision":"approved",
         "reason":"Checked quarterly columns and IFRS source row against issuer filing",
         "evidenceUrl":ROW["sourceUrl"]}
SNAPSHOT={"version":1,"observations":[ROW]}
LEDGER={"version":1,"decisions":[]}
class FinancialReviewTests(unittest.TestCase):
 def test_approval_proposal_has_audit_evidence_but_no_claim_of_authentication(self):
  result,changed=apply_review(REQUEST,SNAPSHOT,LEDGER,TIME)
  self.assertTrue(changed)
  entry=result["decisions"][0]
  self.assertEqual(entry["decision"],"approved")
  self.assertEqual(entry["value"],399.7)
  self.assertIn("PR merge required",entry["authentication"])
  self.assertEqual(LEDGER["decisions"],[])
 def test_duplicate_review_request_is_idempotent(self):
  once,_=apply_review(REQUEST,SNAPSHOT,LEDGER,TIME)
  twice,changed=apply_review(REQUEST,SNAPSHOT,once,TIME)
  self.assertFalse(changed)
  self.assertEqual(len(twice["decisions"]),1)
 def test_changed_sha_blocks_stale_decision(self):
  req={**REQUEST,"sourceSha256":"b"*64}
  with self.assertRaisesRegex(ValueError,"version"):apply_review(req,SNAPSHOT,LEDGER,TIME)
 def test_revised_documents_never_get_silent_approval(self):
  revised=copy.deepcopy(SNAPSHOT)
  revised["observations"][0]["revisedSource"]=True
  revised["observations"][0]["reviewStatus"]="needs-reconciliation"
  with self.assertRaisesRegex(ValueError,"reconciliation"):apply_review(REQUEST,revised,LEDGER,TIME)
  request={**REQUEST,"decision":"needs-reconciliation"}
  out,_=apply_review(request,revised,LEDGER,TIME)
  self.assertEqual(out["decisions"][0]["decision"],"needs-reconciliation")
 def test_manual_rejection_requires_reason_and_preserves_previous_event(self):
  old,_=apply_review(REQUEST,SNAPSHOT,LEDGER,TIME)
  request={**REQUEST,"decision":"rejected","reason":"Cross-checked source column failed"}
  result,_=apply_review(request,SNAPSHOT,old,TIME)
  self.assertEqual([e["decision"] for e in result["decisions"]],["approved","rejected"])
 def test_bad_actor_data_and_untrusted_issuer_body_fail(self):
  for req in [{**REQUEST,"evidenceUrl":"http://unsafe"}, {**REQUEST,"reason":""}, {**REQUEST,"decision":"unknown"},
              {**REQUEST,"observationId":"observation:missing"}]:
   with self.assertRaises(ValueError):apply_review(req,SNAPSHOT,LEDGER,TIME)
 def test_approval_fails_without_accounting_definition_and_numeric_value(self):
  for key,value in [("basis",""),("value",float("nan")),("sourceUrl","http://unsafe")]:
   source=copy.deepcopy(SNAPSHOT)
   source["observations"][0][key]=value
   with self.assertRaises(ValueError):apply_review(REQUEST,source,LEDGER,TIME)

if __name__=="__main__":
 unittest.main()
