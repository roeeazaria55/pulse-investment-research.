import hashlib
import json
import unittest
from pathlib import Path
from report_review_queue import version_id
from research_update_proposals import build_proposals as validated_build_proposals

REGISTRY = json.loads(Path("public/data/official-registry.json").read_text())
URL = "https://rss.globenewswire.com/news-release/test"
COMPANY_ID = "us-dlo-nasdaq-a"
REPORT_ID = "report:" + hashlib.sha256((COMPANY_ID + "|" + URL).encode()).hexdigest()[:32]
SOURCE_SHA = 'a' * 64
REVIEW_ID = version_id(COMPANY_ID, REPORT_ID, SOURCE_SHA)
def observation_id(review_id, metric_id="revenue", start="2026-04-01", end="2026-06-30"):
 return "observation:" + hashlib.sha256((review_id+"|"+metric_id+"|"+start+"|"+end).encode()).hexdigest()[:32]
def build_proposals(snapshot, comparison, ledger):
 return validated_build_proposals(snapshot, comparison, ledger, REGISTRY)
O={"id":observation_id(REVIEW_ID),"companyId":"us-dlo-nasdaq-a","reviewVersionId":REVIEW_ID,"reportId":REPORT_ID,"metricId":"revenue",
   "value":399.7,"unit":"USD million","sourceRaw":"399.7","period":"2026-Q2",
   "periodStart":"2026-04-01","periodEnd":"2026-06-30",
   "basis":"IFRS revenue (rounded)","sourceSha256":SOURCE_SHA,
   "sourceUrl":URL,
   "publishedDate":"2026-08-13","reviewStatus":"needs-reconciliation"}
class ResearchBriefTests(unittest.TestCase):
 def test_pending_source_is_not_called_approved_or_ai_analysis(self):
  output=build_proposals({"observations":[O]},{"results":[]},{"decisions":[]})
  entry=output["proposals"][0]
  self.assertFalse(entry["aiAnalysisEnabled"])
  self.assertEqual(entry["status"],"review-only")
  self.assertEqual(entry["evidence"][0]["approvalStatus"],"needs-reconciliation")
  self.assertEqual(entry["evidence"][0]["raw"],"399.7")
  self.assertIn("אין שינוי",entry["valuationAction"])
 def test_new_source_version_is_a_distinct_brief_not_a_silent_overwrite(self):
  new_review=version_id(O["companyId"],REPORT_ID,"b"*64)
  another={**O,"id":observation_id(new_review),"reviewVersionId":new_review,"sourceSha256":"b"*64}
  out=build_proposals({"observations":[O,another]},{"results":[]},{"decisions":[]})
  self.assertEqual(len(out["proposals"]),2)
 def test_authenticated_review_ledger_requires_exact_source_hash(self):
  wrong={"observationId":O["id"],"decision":"approved","sourceSha256":"c"*64}
  output=build_proposals({"observations":[O]},{},{"decisions":[wrong]})
  self.assertEqual(output["proposals"][0]["evidence"][0]["approvalStatus"],"needs-reconciliation")
 def test_comparison_is_explained_as_pending_not_fabricated(self):
  result=build_proposals({"observations":[O]},{"results":[{"observationId":O["id"],"status":"blocked","reasons":["Review Decision Recorded; not verified"]}]},{})
  self.assertEqual(result["proposals"][0]["evidence"][0]["forecastComparisonStatus"],"blocked")
  self.assertIn("not verified",result["proposals"][0]["evidence"][0]["forecastComparisonReasons"][0])
 def test_same_digest_forged_approval_does_not_promote_reconciliation(self):
  forged={"observationId":O["id"],"decision":"approved","sourceSha256":SOURCE_SHA}
  result=build_proposals({"observations":[O]},{},{"decisions":[forged]})
  self.assertEqual(result["proposals"][0]["evidence"][0]["approvalStatus"],"needs-reconciliation")
  self.assertFalse(result["proposals"][0]["aiAnalysisEnabled"])
 def test_mutable_comparable_claim_cannot_be_displayed_as_valid(self):
  result=build_proposals({"observations":[O]},{"results":[{"observationId":O["id"],"status":"comparable","difference":5000,"percent":100}]},{})
  evidence=result["proposals"][0]["evidence"][0]
  self.assertEqual(evidence["forecastComparisonStatus"],"blocked")
  self.assertTrue(any("Unverified" in x for x in evidence["forecastComparisonReasons"]))
  self.assertNotIn("difference",evidence)
 def test_mixed_source_rows_under_same_version_fail_closed(self):
  for field,other in [("sourceUrl","https://example.org/forged"),
                      ("reportId","report:other"),("period","2026-Q3")]:
   bad={**O,"id":"observation:other","metricId":"capex",field:other}
   with self.assertRaises(ValueError):
    build_proposals({"observations":[O,bad]},{},{})
 def test_digest_and_review_identity_must_match(self):
  for field,value in [("sourceSha256","b"*64),
                      ("reviewVersionId","review:forged"),
                      ("sourceSha256","bad"),
                      ("reviewStatus","approved"),
                      ("reviewStatus","rejected")]:
   with self.assertRaises(ValueError):
    build_proposals({"observations":[{**O,field:value}]},{},{})
 def test_duplicate_observations_are_rejected(self):
  with self.assertRaisesRegex(ValueError,"Duplicate"):
   build_proposals({"observations":[O,O]},{},{})
 def test_real_dlo_observations_remain_reconciliation_only(self):
  snap=json.loads(Path("public/data/auto-financial-observations.json").read_text())
  result=build_proposals(snap,{"results":[]},{"decisions":[]})
  dlo=[p for p in result["proposals"] if p["companyId"]=="us-dlo-nasdaq-a"]
  self.assertEqual(len(dlo),1)
  self.assertEqual(len(dlo[0]["evidence"]),4)
  self.assertTrue(all(e["approvalStatus"]=="needs-reconciliation" for e in dlo[0]["evidence"]))
 def test_report_and_observation_ids_are_derived_from_real_issuer_evidence(self):
  for field,value in [
   ("reportId","report:forged"),
   ("id","observation:forged"),
   ("sourceUrl","https://evil.example/news-release/test"),
   ("sourceUrl","http://rss.globenewswire.com/news-release/test"),
   ("sourceUrl","https://rss.globenewswire.com.evil.example/news-release/test"),
   ("sourceUrl","https://rss.globenewswire.com/news-release/other"),
   ("companyId","fake-company")]:
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):
    build_proposals({"observations":[{**O,field:value}]},{},{})
 def test_numeric_values_units_and_dates_fail_closed(self):
  for field,value in [
   ("value",float("nan")),("value",float("inf")),("value",True),
   ("value","399.7"),("unit",None),("basis",""),("sourceRaw",None),
   ("periodStart","2026-99-01"),("periodEnd","2026-01-01")]:
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):
    build_proposals({"observations":[{**O,field:value}]},{},{})
 def test_registry_is_required_and_cannot_silently_trust_unauthorized_sources(self):
  with self.assertRaisesRegex(ValueError,"registry"):
   validated_build_proposals({"observations":[O]},{},{},None)
  with self.assertRaises(ValueError):
   validated_build_proposals({"observations":[O]},{},{},{"companies":[]})
if __name__=="__main__":unittest.main()
