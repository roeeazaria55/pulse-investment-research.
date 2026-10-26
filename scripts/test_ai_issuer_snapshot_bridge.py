"""Zero-cost issuer AI data bridge: all 12 companies, never approvals or targets.

Tests contain synthetic evidence and must never masquerade as an issuer fetch.
The real GitHub Action produces the snapshot from the official collector first.
"""
import copy
import json
import unittest

from ai_research_packets import ROOT, TICKERS, build_all, source_bound_issuer_research


class IssuerAIPacketBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(
            (ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))
        cls.meta = next(c for c in cls.registry["companies"] if c["id"] == "us-meta-nasdaq-a")
        cls.ftai = next(c for c in cls.registry["companies"] if c["id"] == "candidate-ftai")

    def sample(self):
        url = "https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx"
        metric = {
            "id": "revenue", "value": 64601.0, "previousValue": 51242.0,
            "unit": "USD million", "periodStart": "2026-07-01", "periodEnd": "2026-09-30",
            "previousPeriodStart": "2025-07-01", "previousPeriodEnd": "2025-09-30",
            "sourceRow": "CONDENSED CONSOLIDATED STATEMENTS OF INCOME: Revenue",
            "sourceRaw": "$ 64,601", "sourceUrl": url,
            "accountingBasis": "Issuer Q3 GAAP revenue (unaudited)",
            "comparison": "Exact previous-year quarter, not prediction",
            "reviewStatus": "pending-review",
            "sourcePage": None,
        }
        return {
            "version": 1,
            "reports": [{
                "companyId": self.meta["id"], "status": "pending-review",
                "aiAnalysisEnabled": False, "reviewRequired": True,
                "sourceUrl": url, "sourceVersion": "a"*64,
                "sourceDigestKind": "retained-issuer-html-table-sha256",
                "reportPeriod": "2026-07-01/2026-09-30",
                "publishedDate": "2026-10-21",
                "contentId": "f"*24,
                "metrics": [metric],
                "findings": ["שינוי בהכנסות מבוסס מקור — ממתין לבדיקה."],
                "questions": ["האם הגידול בהכנסות תומך בהנחות המודל?"],
            }]
        }

    def test_all_12_official_issuers_have_unique_usable_packet_keys(self):
        keys = [c["ticker"] or c["id"] for c in self.registry["companies"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 12)
        self.assertEqual(tuple(keys), TICKERS)
        packets = build_all()
        self.assertEqual(set(packets), set(keys))
        self.assertEqual(packets["candidate-enlight"]["ticker"], "")
        self.assertFalse(packets["candidate-enlight"]["trustPolicy"]["mayModifyTargetsOrProbabilities"])
        self.assertEqual(packets["FTAI"]["latestIssuerResearch"]["status"], "not-generated")

    def test_source_bound_meta_is_never_target_approved_or_prediction(self):
        res = source_bound_issuer_research(self.meta, self.sample())
        self.assertEqual(res["status"], "pending-review")
        self.assertFalse(res["modelEligible"])
        m = res["sourceBoundMetrics"][0]
        self.assertEqual((m["value"], m["previousValue"]), (64601.0, 51242.0))
        self.assertEqual(m["sourceDigest"], "a"*64)
        self.assertEqual(m["comparisonType"], "historical-not-prediction")
        self.assertFalse(m["modelEligible"])
        self.assertEqual(res["sourceBoundFindings"],["שינוי בהכנסות מבוסס מקור — ממתין לבדיקה."])
        self.assertEqual(res["humanResearchQuestions"],["האם הגידול בהכנסות תומך בהנחות המודל?"])
        self.assertIs(res["automaticModelChange"],False)
        self.assertEqual(m["periodEnd"], "2026-09-30")

    def test_inaccessible_ftai_is_never_filled_from_ir_link_or_fixture(self):
        missing = {
            "version": 1,
            "reports": [{
                "companyId": self.ftai["id"], "status": "insufficient-evidence",
                "metrics": [], "aiAnalysisEnabled": False, "reviewRequired": True,
                "issuerPortal": "https://ftandi.gcs-web.com/",
            }],
        }
        result = source_bound_issuer_research(self.ftai, missing)
        self.assertEqual(result["sourceBoundMetrics"], [])
        self.assertIsNone(result["report"])
        self.assertFalse(result["modelEligible"])

    def test_reject_issuer_spoofing_and_source_relabeling(self):
        for field, injected in [
            ("sourceUrl", "https://investor.atmeta.com.evil.test/latest"),
            ("sourceVersion", "0000"),
            ("sourceDigestKind", "original-pdf-sha256"),
            ("status", "approved"),
            ("reviewRequired", False),
            ("aiAnalysisEnabled", True),
        ]:
            with self.subTest(field=field):
                data = self.sample()
                data["reports"][0][field] = injected
                with self.assertRaises(ValueError):
                    source_bound_issuer_research(self.meta, data)

    def test_reject_nonfinite_wrong_currency_ambiguous_or_forecast_rows(self):
        for field, bad in [
            ("value", float("nan")),
            ("value", True),
            ("unit", "ILS million"),
            ("periodStart", "2026-15-01"),
            ("previousPeriodEnd", "2026-10-01"),
            ("reviewStatus", "approved"),
            ("sourceUrl", "https://www.sec.gov/Archives/edgar/data/1590364/a"),
            ("id", "forecastMiss"),
        ]:
            with self.subTest(field=field):
                data = self.sample()
                data["reports"][0]["metrics"][0][field] = bad
                with self.assertRaises(ValueError):
                    source_bound_issuer_research(self.meta, data)
        data = self.sample()
        data["reports"][0]["metrics"].append(
            copy.deepcopy(data["reports"][0]["metrics"][0]))
        with self.assertRaises(ValueError):
            source_bound_issuer_research(self.meta, data)


if __name__ == "__main__":
    unittest.main()
