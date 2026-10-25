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

    def test_source_index_failure_is_not_mislabeled_as_no_new_report(self):
        from latest_research_updates import source_check_summary
        checked = source_check_summary({"sources": [
            {"companyId": "us-dlo-nasdaq-a", "status": "failed",
             "lastAttemptAt": "2026-10-25T11:00:00Z", "lastSuccessfulAt": None},
            {"companyId": "us-dlo-nasdaq-a", "status": "ok",
             "lastAttemptAt": "2026-10-25T11:00:00Z",
             "lastSuccessfulAt": "2026-10-25T11:00:00Z"},
            {"companyId": "candidate-nebius", "status": "ok",
             "lastAttemptAt": "2026-10-25T11:00:00Z", "lastSuccessfulAt": "2026-10-25T11:00:00Z"},
        ]})
        self.assertEqual(checked["us-dlo-nasdaq-a"]["status"], "partial")
        self.assertEqual(checked["candidate-nebius"]["status"], "ok")
        self.assertEqual(checked["candidate-iren"]["status"], "unconfigured")
        self.assertEqual(checked["us-dlo-nasdaq-a"]["sourcesFailed"], 1)
        with self.assertRaisesRegex(ValueError, "Unknown issuer"):
            source_check_summary({"sources": [{"companyId": "us-dlo-nasdaq-a", "status": "approved"}]})

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
        registry = json.loads((ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))
        self.assertEqual([r["companyId"] for r in first["reports"]],
                         [c["id"] for c in registry["companies"]])
        self.assertEqual(len(first["reports"]), 12)
        by_company = {r["companyId"]: r for r in first["reports"]}
        self.assertEqual(by_company["candidate-nebius"]["status"], "insufficient-evidence")
        self.assertTrue(by_company["candidate-nebius"]["reportEvidence"])
        self.assertEqual(by_company["us-smci-nasdaq-common"]["status"], "pending-review")
        self.assertTrue(by_company["us-smci-nasdaq-common"]["metrics"])
        self.assertEqual(first["coverage"]["companyCount"], 12)
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

    def test_generic_sec_source_context_does_not_promote_valuation(self):
        by_id = {r["companyId"]: r for r in build(self.dlo, self.iren)["reports"]}
        smci = by_id["us-smci-nasdaq-common"]
        rev = next(x for x in smci["metrics"] if x["id"] == "revenue")
        self.assertEqual(rev["value"], 39063.072)
        self.assertEqual(rev["previousValue"], 21972.042)
        self.assertEqual(rev["reviewStatus"], "pending-review")
        self.assertEqual(smci["sourceVersion"], smci["reportEvidence"]["sha256"])
        self.assertFalse(smci["aiAnalysisEnabled"])
        self.assertTrue(smci["reviewRequired"])
        self.assertEqual(smci["modelReview"], [])

    def test_generic_research_content_id_not_affected_by_fetch_health(self):
        from latest_research_updates import other_issuer_update
        from issuer_coverage import build as build_coverage, read as read_coverage
        import copy
        coverage = build_coverage(
            read_coverage(ROOT / "public/data/official-registry.json"),
            read_coverage(ROOT / "public/data/report-intake.json"))
        row = next(c for c in coverage["coverage"] if c["companyId"] == "us-smci-nasdaq-common")
        first = other_issuer_update(row)
        changed = copy.deepcopy(row)
        changed["intakeStatus"] = "ok" if row["intakeStatus"] != "ok" else "failed"
        changed["report"]["lastSuccessfulAt"] = "2026-10-27T08:00:00Z"
        changed["report"]["sourceIsCurrentlyReachable"] = not row["report"]["sourceIsCurrentlyReachable"]
        self.assertEqual(first["contentId"], other_issuer_update(changed)["contentId"])

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
