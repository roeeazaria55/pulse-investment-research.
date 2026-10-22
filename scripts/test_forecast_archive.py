"""Historical PULSE forecast snapshots are not backdated to research labels."""
import unittest
from forecast_archive import snapshot
T="2026-10-22T12:00:00+00:00"
L="2026-10-23T12:00:00+00:00"
DATA=[{"companyId":"us-dlo-nasdaq-a","ticker":"DLO","asOf":"2026-10-20",
       "metrics":[{"id":"revenue","target":{"value":400.0,"period":"Q3 2026","unit":"USD million","basis":"revenue"}}]}]
class ForecastArchiveTests(unittest.TestCase):
 def test_capture_unverified_asof_but_proven_first_recorded_time(self):
  a=snapshot(DATA,{},T,"abc123")
  self.assertEqual(a["newVersionCount"],1)
  f=a["forecasts"][0]
  self.assertEqual(f["researchAsOf"],"2026-10-20")
  self.assertEqual(f["firstRecordedAt"],T)
  self.assertFalse(f["canBeUsedForHistoricalBacktest"])
  self.assertIn("unverified",f["chronologyStatus"])
 def test_repeated_source_creates_no_new_forecast_and_preserves_time(self):
  first=snapshot(DATA,{},T,"abc123")
  second=snapshot(DATA,first,L,"def456")
  self.assertEqual(second["newVersionCount"],0)
  self.assertEqual(second["forecasts"][0]["firstRecordedAt"],T)
 def test_new_target_creates_new_version_without_mutating_old_value(self):
  a=snapshot(DATA,{},T,"abc123")
  revised=[{**DATA[0],"metrics":[{"id":"revenue","target":{"value":420,"period":"Q3 2026","unit":"USD million","basis":"revenue"}}]}]
  b=snapshot(revised,a,L,"def456")
  self.assertEqual(b["newVersionCount"],1)
  self.assertEqual(len(b["forecasts"]),2)
  self.assertEqual({f["point"]["value"] for f in b["forecasts"]},{400,420})
 def test_rejects_invalid_forecast_values_without_inventing_measurements(self):
  invalid=[{**DATA[0],"metrics":[{"id":"bad","target":{"value":float("nan"),"period":"Q3 2026","unit":"USD million","basis":"revenue"}}]}]
  self.assertEqual(snapshot(invalid,{},T,"abc123")["forecasts"],[])
 def test_no_historical_prospective_comparison_is_claimed_from_asof(self):
  r=snapshot(DATA,{},T,"abc123")
  self.assertGreater(r["forecasts"][0]["firstRecordedAt"][:10],r["forecasts"][0]["researchAsOf"])
if __name__=="__main__":unittest.main()
