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

    def test_dlo_observation_must_match_retained_report_digest_and_identity(self):
        tampered = json.loads(json.dumps(self.dlo))
        target = next(x for x in tampered["observations"] if x["metricId"] == "revenue")
        target["sourceSha256"] = "f" * 64
        actual = dlo_update(tampered)
        self.assertNotIn("revenue", {x["id"] for x in actual["metrics"]})
        target["sourceSha256"] = next(x["sourceSha256"] for x in self.dlo["observations"] if x["metricId"] == "revenue")
        target["reportId"] = "report:forged"
        actual = dlo_update(tampered)
        self.assertNotIn("revenue", {x["id"] for x in actual["metrics"]})

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


    def test_real_model_and_research_comparisons_are_explicitly_non_comparable(self):
        reports = {r["ticker"]: r for r in build(self.dlo, self.iren)["reports"]}
        iren = reports["IREN"]
        self.assertEqual(iren["sourceDigestKind"], "curated-extract-json-sha256-not-original-pdf")
        review = {r["metricId"]: r for r in iren["modelReview"]}
        self.assertEqual(review["revenue"]["modelValue"], 4500)
        self.assertEqual(review["operatingCash"]["modelValue"], 1400)
        self.assertEqual(review["capex"]["modelValue"], 17000)
        self.assertTrue(all(r["status"] == "not-comparable-period-or-definition" for r in review.values()))
        self.assertTrue(all(r["automaticChange"] is False for r in review.values()))
        source = {m["id"]: m for m in iren["metrics"]}
        self.assertEqual(source["revenue"]["sourceRaw"], "707.0")
        self.assertEqual(source["revenue"]["sourcePreviousRaw"], "501.0")
        self.assertEqual(source["revenue"]["sourcePage"], 12)
        self.assertIn("(2,998.0)", source["capex"]["sourceRaw"])
        self.assertIn("(1,335.1)", source["capex"]["sourceRaw"])
        self.assertEqual(source["capex"]["sourcePage"], 14)
        dlo = {r["metricId"]: r for r in reports["DLO"]["modelReview"]}
        self.assertEqual(dlo["grossProfit"]["modelValue"], 650)
        self.assertTrue(dlo["revenue"]["researchTextMatch"])
        self.assertEqual(reports["DLO"]["status"], "needs-reconciliation")
        self.assertEqual(reports["DLO"]["activeValuationContext"]["baseTargetPerShare"], 21.14)
        self.assertEqual(dlo["grossProfit"]["modelStatus"], "archived-secondary")

    def test_malformed_pdf_pointer_fails_closed(self):
        changed = json.loads(json.dumps(self.iren))
        changed["pdfUrl"] = "https://attacker.invalid/report.pdf"
        r = iren_update(changed)
        self.assertEqual(r["status"], "insufficient-evidence")
        self.assertFalse(r["metrics"])

    def test_issuer_model_identity_is_checked_not_silently_combined(self):
        from unittest.mock import patch
        from latest_research_updates import model_context
        real_load = __import__("latest_research_updates").load
        def corrupted(path):
            value = real_load(path)
            if str(path).endswith("models/iren.json"):
                value["companyId"] = "candidate-nebius"
            return value
        with patch("latest_research_updates.load", side_effect=corrupted):
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                model_context(iren_update(self.iren))


if __name__ == "__main__":
    unittest.main()
