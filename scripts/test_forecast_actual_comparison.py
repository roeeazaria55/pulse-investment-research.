import unittest
from forecast_actual_comparison import compare,evaluate
FORECAST={"id":"forecast:test","companyId":"us-dlo-nasdaq-a","metricId":"revenue",
          "point":{"value":400,"period":"2026-Q2","unit":"USD million","basis":"IFRS revenue"},
          "researchAsOf":"2026-07-30","firstRecordedAt":"2026-07-31T00:00:00+00:00"}
ACTUAL={"id":"observation:test","companyId":"us-dlo-nasdaq-a","metricId":"revenue",
        "value":440,"period":"2026-Q2","unit":"USD million","basis":"IFRS revenue",
        "publishedDate":"2026-08-13","sourceSha256":"a"*64}
APPROVAL={"observationId":ACTUAL["id"],"sourceSha256":ACTUAL["sourceSha256"],"decision":"approved"}
class ForecastActualTests(unittest.TestCase):
 def test_valid_prospective_checked_comparison(self):
  result=compare(FORECAST,ACTUAL,[APPROVAL])
  self.assertEqual(result["status"],"comparable")
  self.assertEqual(result["difference"],40)
  self.assertEqual(result["percent"],10)
 def test_rejects_backdated_user_research_date_as_proof(self):
  f={**FORECAST,"firstRecordedAt":"2026-10-22T00:00:00Z"}
  result=compare(f,ACTUAL,[APPROVAL])
  self.assertEqual(result["status"],"blocked")
  self.assertIsNone(result["difference"])
  self.assertTrue(any("archived before" in r for r in result["reasons"]))
 def test_rejects_same_day_or_unknown_forecast_timestamp(self):
  for instant in ("2026-08-13T00:00:00Z",None):
   r=compare({**FORECAST,"firstRecordedAt":instant},ACTUAL,[APPROVAL])
   self.assertEqual(r["status"],"blocked")
 def test_rejects_unapproved_or_superseded_source(self):
  self.assertEqual(compare(FORECAST,ACTUAL,[])["status"],"blocked")
  self.assertEqual(compare(FORECAST,ACTUAL,[{**APPROVAL,"sourceSha256":"b"*64}])["status"],"blocked")
  self.assertEqual(compare(FORECAST,ACTUAL,[APPROVAL,{**APPROVAL,"decision":"rejected"}])["status"],"blocked")
 def test_company_metric_period_unit_and_accounting_basis_are_strict(self):
  for k,v in [("companyId","candidate-nebius"),("metricId","grossProfit"),
              ("period","2026-Q3"),("unit","USD billion"),("basis","Adjusted EBITDA")]:
   a={**ACTUAL,k:v}
   self.assertEqual(compare(FORECAST,a,[{**APPROVAL,"observationId":a["id"]}])["status"],"blocked")
 def test_zero_target_preserves_null_percentage(self):
  f={**FORECAST,"point":{**FORECAST["point"],"value":0}}
  self.assertIsNone(compare(f,ACTUAL,[APPROVAL])["percent"])
 def test_empty_approved_ledger_has_no_claimed_forecast_success(self):
  out=evaluate({"forecasts":[FORECAST]},{"observations":[ACTUAL]},{"decisions":[]})
  self.assertEqual(out["results"][0]["status"],"blocked")
if __name__=="__main__":unittest.main()
