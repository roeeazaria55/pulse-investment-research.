"""Real retained issuer evidence + fail-closed research update regression tests."""
from pathlib import Path
import json
import unittest
from latest_research_updates import build, dlo_update, iren_update, ROOT


class LatestResearchUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iren = json.loads((ROOT / "public/data/iren-fy26-source.json").read_text(encoding="utf-8"))
        cls.dlo = json.loads((ROOT / "public/data/auto-financial-observations.json").read_text(encoding="utf-8"))

    def test_real_iren_source_and_prior_year_changes(self):
        r = iren_update(self.iren)
        self.assertEqual(r["status"], "historical-baseline-pending-review")
        metrics = {m["id"]: m for m in r["metrics"]}
        self.assertEqual(metrics["revenue"]["value"], 707.0)
        self.assertEqual(metrics["revenue"]["previousValue"], 501.0)
        self.assertEqual(metrics["operatingCash"]["value"], 2100.4)
        self.assertEqual(metrics["capex"]["value"], 4333.1)
        self.assertEqual(metrics["capex"]["previousValue"], 1372.7)
        self.assertFalse(r["aiAnalysisEnabled"])
        self.assertTrue(r["reviewRequired"])
        self.assertIn("אין שינוי", r["modelChange"])

    def test_real_dlo_snapshot_never_promoted_or_backtested(self):
        r = dlo_update(self.dlo)
        self.assertIn(r["status"], ("needs-reconciliation", "pending-review"))
        self.assertTrue(r["metrics"])
        self.assertTrue(all(m["previousValue"] is None and m["changePercent"] is None for m in r["metrics"]))
        self.assertTrue(all(m["reviewStatus"] in ("needs-reconciliation", "pending-review") for m in r["metrics"]))
        self.assertFalse(r["aiAnalysisEnabled"])

    def test_malformed_dlo_evidence_not_displayed(self):
        r = dlo_update({"observations": [{
            "companyId": "us-dlo-nasdaq-a", "metricId": "revenue", "value": 1,
            "unit": "USD million", "sourceUrl": "https://attacker.invalid/report",
            "sourceSha256": "a" * 64, "reviewStatus": "pending-review"
        }]})
        self.assertEqual(r["status"], "insufficient-evidence")
        self.assertEqual(r["metrics"], [])

    def test_iren_missing_source_row_is_not_invented(self):
        changed = json.loads(json.dumps(self.iren))
        changed["tables"][0]["rows"] = []
        with self.assertRaises(ValueError):
            iren_update(changed)

    def test_deterministic_content_ids_and_missing_data(self):
        first = build(self.dlo, self.iren)
        second = build(self.dlo, self.iren)
        self.assertEqual([r["contentId"] for r in first["reports"]],
                         [r["contentId"] for r in second["reports"]])
        self.assertEqual([r["ticker"] for r in first["reports"]], ["DLO", "IREN", "NBIS", "SMCI"])
        self.assertTrue(all(not r["metrics"] for r in first["reports"][2:]))
        self.assertEqual(first["aiStatus"], "not-enabled")


if __name__ == "__main__":
    unittest.main()
