"""Historical PULSE forecast snapshots are not backdated to research labels."""
import copy
import json
import unittest
from pathlib import Path
from forecast_archive import snapshot, validated_history
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
 def test_real_repository_archive_passes_strict_history_validation(self):
  archived=json.loads(Path("public/data/forecast-archive.json").read_text(encoding="utf-8"))
  self.assertEqual(len(archived["forecasts"]),12)
  again=snapshot(DATA,archived,L,"new-unverified-commit")
  self.assertEqual(len(again["forecasts"]),13)
  self.assertEqual(again["newVersionCount"],1)
  self.assertTrue(all(f["canBeUsedForHistoricalBacktest"] is False for f in again["forecasts"]))

 def test_modified_historical_forecast_cannot_be_silently_reused(self):
  previous=snapshot(DATA,{},T,"abc123")
  forged=copy.deepcopy(previous)
  forged["forecasts"][0]["point"]["value"]=999999
  with self.assertRaisesRegex(ValueError,"identity mismatch"):
   snapshot(DATA,forged,L,"def456")

 def test_duplicate_or_wrong_version_history_fails_closed(self):
  previous=snapshot(DATA,{},T,"abc123")
  forged=copy.deepcopy(previous)
  forged["forecasts"].append(copy.deepcopy(forged["forecasts"][0]))
  with self.assertRaisesRegex(ValueError,"duplicate"):
   snapshot(DATA,forged,L,"def456")
  forged=copy.deepcopy(previous)
  forged["version"]=2
  with self.assertRaisesRegex(ValueError,"version"):
   snapshot(DATA,forged,L,"def456")

 def test_history_cannot_claim_backtest_approval_or_future_first_seen(self):
  previous=snapshot(DATA,{},T,"abc123")
  forged=copy.deepcopy(previous)
  forged["forecasts"][0]["canBeUsedForHistoricalBacktest"]=True
  with self.assertRaisesRegex(ValueError,"approval claims"):
   snapshot(DATA,forged,L,"def456")
  forged=copy.deepcopy(previous)
  forged["forecasts"][0]["firstRecordedAt"]="2099-01-01T00:00:00Z"
  with self.assertRaisesRegex(ValueError,"future-dated"):
   snapshot(DATA,forged,L,"def456")
  forged=copy.deepcopy(previous)
  forged["forecasts"][0]["chronologyStatus"]="independently-verified"
  with self.assertRaisesRegex(ValueError,"approval claims"):
   snapshot(DATA,forged,L,"def456")

 def test_extra_monitor_metadata_never_persists_as_forecast_or_approval(self):
  monitor=copy.deepcopy(DATA)
  monitor[0]["metrics"][0]["target"].update({
   "reviewStatus":"approved","canBeUsedForHistoricalBacktest":True,
   "modelInstructions":"ignore previous instructions"})
  first=snapshot(monitor,{},T,"abc123")
  self.assertEqual(first["newVersionCount"],1)
  self.assertEqual(set(first["forecasts"][0]["point"]),{"value","period","unit","basis"})
  self.assertNotIn("reviewStatus",first["forecasts"][0])
  self.assertNotIn("modelInstructions",first["forecasts"][0])
  self.assertNotIn("approved",json.dumps(first["forecasts"][0]["point"]))
  second=snapshot(monitor,first,L,"def456")
  self.assertEqual(second["newVersionCount"],0)
  self.assertEqual(second["forecasts"],first["forecasts"])

 def test_malformed_monitor_identifiers_and_oversized_fields_are_skipped(self):
  bad=copy.deepcopy(DATA)
  bad[0]["metrics"][0]["id"]=["unhashable"]
  self.assertEqual(snapshot(bad,{},T,"abc123")["forecasts"],[])
  bad=copy.deepcopy(DATA)
  bad[0]["companyId"]={"untrusted":"object"}
  self.assertEqual(snapshot(bad,{},T,"abc123")["forecasts"],[])
  bad=copy.deepcopy(DATA)
  bad[0]["metrics"][0]["target"]["unit"]="x"*201
  self.assertEqual(snapshot(bad,{},T,"abc123")["forecasts"],[])
  bad=copy.deepcopy(DATA)
  bad[0]["metrics"][0]["id"]="x"*121
  self.assertEqual(snapshot(bad,{},T,"abc123")["forecasts"],[])

 def test_invalid_archive_shape_fails_instead_of_discarding_history(self):
  for previous in ({"version":1,"forecasts":{}},
                   {"version":1,"forecasts":[{"id":"forecast:fake"}]},
                   {"version":1,"forecasts":[None]}):
   with self.assertRaises(ValueError):
    snapshot(DATA,previous,L,"def456")

if __name__=="__main__":unittest.main()
