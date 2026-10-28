"""Coverage must never confuse readable issuer documents with verified metrics."""
import copy
import unittest
from issuer_coverage import ROOT, build, read, safe_source_facts, document_usable, report_rank


class CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read(ROOT / "public/data/official-registry.json")
        cls.intake = read(ROOT / "public/data/report-intake.json")

    def test_all_12_registered_issuers_have_explicit_state(self):
        rows = build(self.registry, self.intake)["coverage"]
        self.assertEqual(len(rows), 12)
        self.assertEqual({x["companyId"] for x in rows},
                         {c["id"] for c in self.registry["companies"]})
        for r in rows:
            self.assertIn(r["intakeStatus"], ("ok", "partial", "failed", "no-candidates", "unconfigured"))
            self.assertIn(r["metricCoverage"], ("no-document", "report-only", "provisional-structured"))
            self.assertEqual(bool(r["typedMetrics"]), r["metricCoverage"] == "provisional-structured")

    def test_structured_smci_duration_and_prior_comparable_in_same_tag(self):
        rows = build(self.registry, self.intake)["coverage"]
        smci = next(r for r in rows if r["companyId"] == "us-smci-nasdaq-common")
        self.assertEqual(smci["metricCoverage"], "provisional-structured")
        actual = {m["id"]: m for m in smci["typedMetrics"]}
        self.assertEqual(actual["revenue"]["value"], 39063.072)
        self.assertEqual(actual["revenue"]["previousValue"], 21972.042)
        self.assertEqual(actual["revenue"]["periodStart"], "2025-07-01")
        self.assertEqual(actual["revenue"]["periodEnd"], "2026-06-30")
        self.assertEqual(actual["revenue"]["previousPeriodStart"], "2024-07-01")
        self.assertEqual(actual["revenue"]["sourceSha256"], smci["report"]["sha256"])
        self.assertEqual(actual["revenue"]["reviewStatus"], "pending-review")
        self.assertTrue(all("surprise" not in m["id"] for m in smci["typedMetrics"]))

    def test_smci_operating_and_net_income_same_adjacent_fiscal_period(self):
        rows = build(self.registry, self.intake)["coverage"]
        smci = next(r for r in rows if r["companyId"] == "us-smci-nasdaq-common")
        data = {m["id"]: m for m in smci["typedMetrics"]}
        self.assertEqual(len(data), 8)
        self.assertEqual(data["operatingIncome"]["value"], 2770.486)
        self.assertEqual(data["operatingIncome"]["previousValue"], 1252.994)
        self.assertEqual(data["netIncome"]["value"], 2230.453)
        self.assertEqual(data["netIncome"]["previousValue"], 1048.854)
        self.assertEqual(data["cash"]["value"], 7521.474)
        self.assertEqual(data["cash"]["previousValue"], 5169.911)
        self.assertEqual(data["inventory"]["value"], 12895.949)
        self.assertEqual(data["inventory"]["previousValue"], 4680.375)
        self.assertEqual(data["accountsReceivable"]["value"], 6125.414)
        self.assertEqual(data["accountsReceivable"]["previousValue"], 2203.942)
        for item in ("cash","inventory","accountsReceivable"):
            self.assertEqual(data[item]["periodStart"],"2026-06-30")
            self.assertEqual(data[item]["periodEnd"],"2026-06-30")
            self.assertEqual(data[item]["previousPeriodEnd"],"2025-06-30")
            self.assertIn("point-in-time",data[item]["accountingBasis"])
            self.assertEqual(data[item]["reviewStatus"],"pending-review")
            self.assertEqual(data[item]["sourceSha256"],smci["report"]["sha256"])
        self.assertEqual(data["operatingCash"]["value"], -6809.886)
        self.assertEqual(data["operatingCash"]["previousValue"], 1659.524)
        for metric in ("operatingIncome", "netIncome", "operatingCash"):
            self.assertEqual(data[metric]["periodStart"], "2025-07-01")
            self.assertEqual(data[metric]["periodEnd"], "2026-06-30")
            self.assertEqual(data[metric]["previousPeriodEnd"], "2025-06-30")
            self.assertEqual(data[metric]["sourceSha256"], smci["report"]["sha256"])
            self.assertEqual(data[metric]["reviewStatus"], "pending-review")

    def test_strict_pdf_adapter_never_confuses_unreviewed_layouts(self):
        rows = build(self.registry, self.intake)["coverage"]
        nbis = next(r for r in rows if r["companyId"] == "candidate-nebius")
        self.assertEqual(nbis["metricCoverage"], "provisional-structured")
        self.assertGreaterEqual(len(nbis["typedMetrics"]), 1)
        revenue=nbis["typedMetrics"][0]
        self.assertEqual(revenue["id"], "revenue")
        self.assertEqual(revenue["value"], 582.3)
        self.assertEqual(revenue["previousValue"], 105.1)
        self.assertEqual(revenue["sourcePage"], 7)
        self.assertEqual(revenue["sourceSha256"], nbis["report"]["sha256"])
        self.assertIsNotNone(nbis["report"])

    def test_sandisk_fiscal_q4_not_calendar_q2(self):
        rows=build(self.registry,self.intake)["coverage"]
        sndk=next(r for r in rows if r["companyId"]=="candidate-sandisk")
        metrics={m["id"]:m for m in sndk["typedMetrics"]}
        self.assertEqual(metrics["revenue"]["value"], 8965)
        self.assertEqual(metrics["revenue"]["previousValue"], 1901)
        self.assertEqual(metrics["revenue"]["periodEnd"], "2026-07-03")
        self.assertEqual(metrics["revenue"]["previousPeriodEnd"], "2025-06-27")
        self.assertEqual(metrics["operatingIncome"]["value"], 7037)
        self.assertEqual(metrics["operatingIncome"]["previousValue"], 18)
        self.assertTrue(all(m["reviewStatus"]=="pending-review" for m in metrics.values()))

    def test_conference_remarks_not_financial_filing(self):
        registry = next(c for c in self.registry["companies"] if c["id"] == "candidate-enlight")
        dummy = {
            "companyId": registry["id"],
            "status": "extracted", "sha256": "a"*64,
            "id": "report:"+"b"*32, "format": "pdf",
            "title": "Enlight Renewable Energy Q2 2026 conference call prepared remarks",
            "url": "https://enlightenergy.com/wp-content/uploads/2026/08/Enlight-prepared-remarks-Q2-2026-1.pdf",
            "tables": [{"rows": [["Revenues", "210"]]}],
        }
        self.assertFalse(document_usable(dummy, registry))
        self.assertEqual(build(self.registry, {
            "documents": [dummy], "sources": [],
        })["coverage"][8]["metricCoverage"], "no-document")

    def test_brainsway_three_months_matched_in_exact_issuer_table(self):
        rows = build(self.registry, self.intake)["coverage"]
        bway = next(r for r in rows if r["companyId"] == "candidate-brainsway")
        metrics = {m["id"]:m for m in bway["typedMetrics"]}
        self.assertEqual(bway["metricCoverage"], "provisional-structured")
        self.assertEqual(metrics["revenue"]["value"], 17.107)
        self.assertEqual(metrics["revenue"]["previousValue"], 12.632)
        self.assertEqual(metrics["grossProfit"]["value"], 12.766)
        self.assertEqual(metrics["revenue"]["periodStart"], "2026-04-01")
        self.assertEqual(metrics["revenue"]["periodEnd"], "2026-06-30")
        self.assertEqual(metrics["revenue"]["previousPeriodStart"], "2025-04-01")
        self.assertEqual(metrics["revenue"]["evidenceScope"], "retained-issuer-html-table")
        self.assertTrue(all(m["reviewStatus"] == "pending-review" for m in metrics.values()))

    def test_deny_unknown_domains_and_tampered_hash(self):
        company = next(c for c in self.registry["companies"] if c["id"] == "candidate-nebius")
        doc = next(d for d in self.intake["documents"] if d["companyId"] == company["id"])
        bad = copy.deepcopy(doc)
        bad["url"] = "https://evil.example/Archives/edgar/data/1375365/one.pdf"
        self.assertFalse(document_usable(bad, company))
        bad = copy.deepcopy(doc)
        bad["sha256"] = "invalid"
        self.assertFalse(document_usable(bad, company))

    def test_ambiguous_sec_context_fails_closed_without_metric(self):
        doc = next(d for d in self.intake["documents"] if d["companyId"] == "us-smci-nasdaq-common")
        bad = copy.deepcopy(doc)
        revenue = next(f for f in bad["facts"] if f["concept"] == "us-gaap:revenuefromcontractwithcustomerexcludingassessedtax"
                       and f["end"] == "2026-06-30")
        bad["facts"].append(copy.deepcopy(revenue))
        metrics = {m["id"]: m for m in safe_source_facts(bad)}
        self.assertNotIn("revenue", metrics)

    def test_nonadjacent_prior_fiscal_year_is_not_comparable(self):
        smci = next(d for d in self.intake["documents"] if d["companyId"] == "us-smci-nasdaq-common")
        missing_2025 = copy.deepcopy(smci)
        missing_2025["facts"] = [f for f in missing_2025["facts"] if not (
            f.get("concept") == "us-gaap:revenuefromcontractwithcustomerexcludingassessedtax" and
            f.get("end") == "2025-06-30")]
        fact = next(x for x in safe_source_facts(missing_2025) if x["id"] == "revenue")
        self.assertIsNone(fact["previousValue"])
        self.assertIsNone(fact["changePercent"])

    def test_yoy_data_is_never_inferred_from_pdf_column_order(self):
        smci = next(d for d in self.intake["documents"] if d["companyId"] == "us-smci-nasdaq-common")
        forged = copy.deepcopy(smci)
        forged["facts"] = []
        self.assertEqual(safe_source_facts(forged), [])

    def test_new_report_can_be_added_without_hardcoding_company(self):
        added = copy.deepcopy(self.intake)
        reg = next(c for c in self.registry["companies"] if c["id"] == "candidate-enlight")
        template = next(d for d in self.intake["documents"] if d["companyId"] == "candidate-nebius")
        doc = copy.deepcopy(template)
        doc.update({"id": "report:" + "a" * 32, "companyId": reg["id"],
                    "url": "https://enlightenergy.com/wp-content/uploads/example.pdf",
                    "title": "Enlight FY2026 official report", "facts": [], "tables": []})
        added["documents"] = [d for d in added["documents"] if d["companyId"] != reg["id"]]
        added["documents"].append(doc)
        coverage = build(self.registry, added)["coverage"]
        enlight = next(r for r in coverage if r["companyId"] == reg["id"])
        self.assertEqual(enlight["report"]["id"], doc["id"])
        self.assertEqual(enlight["metricCoverage"], "report-only")


if __name__ == "__main__":
    unittest.main()
