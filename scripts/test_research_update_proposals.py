import unittest
from research_update_proposals import build_proposals
O={"id":"observation:test","companyId":"us-dlo-nasdaq-a","reviewVersionId":"review:source","metricId":"revenue",
   "value":399.7,"unit":"USD million","sourceRaw":"399.7","period":"2026-Q2",
   "periodStart":"2026-04-01","periodEnd":"2026-06-30",
   "basis":"IFRS revenue (rounded)","sourceSha256":"a"*64,
   "sourceUrl":"https://rss.globenewswire.com/news-release/test",
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
  another={**O,"id":"observation:new","reviewVersionId":"review:new","sourceSha256":"b"*64}
  out=build_proposals({"observations":[O,another]},{"results":[]},{"decisions":[]})
  self.assertEqual(len(out["proposals"]),2)
 def test_authenticated_review_ledger_requires_exact_source_hash(self):
  wrong={"observationId":O["id"],"decision":"approved","sourceSha256":"c"*64}
  output=build_proposals({"observations":[O]},{},{"decisions":[wrong]})
  self.assertEqual(output["proposals"][0]["evidence"][0]["approvalStatus"],"needs-reconciliation")
 def test_comparison_is_explained_as_pending_not_fabricated(self):
  result=build_proposals({"observations":[O]},{"results":[{"observationId":O["id"],"status":"blocked"}]},{})
  self.assertEqual(result["proposals"][0]["evidence"][0]["forecastComparisonStatus"],"blocked")
if __name__=="__main__":unittest.main()
