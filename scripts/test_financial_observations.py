"""Source-backed report extraction tests: synthetic mutations and real stored intake."""
import copy
import json
import unittest
from pathlib import Path

from financial_observations import extract, amount

ROOT = Path("public/data")
REGISTRY = json.loads((ROOT/"official-registry.json").read_text())
SNAPSHOT = json.loads((ROOT/"report-intake.json").read_text())
DLO = next(d for d in SNAPSHOT["documents"] if d["companyId"] == "us-dlo-nasdaq-a" and "second-quarter-2026" in d["url"])


class AutomaticFinancialObservationTests(unittest.TestCase):
    def run_extract(self, doc=None, previous=None):
        snapshot = {"generatedAt":SNAPSHOT["generatedAt"],"documents":[doc or DLO]}
        return extract(snapshot, REGISTRY, previous)

    def test_existing_real_issuer_snapshot_yields_four_rows_without_hardcoded_values(self):
        result = self.run_extract()
        values = {o["metricId"]: o["value"] for o in result["observations"]}
        self.assertEqual(values, {"revenue":399.7,"grossProfit":127.2,"operatingCash":140.522,"capex":9.91})
        for observation in result["observations"]:
            self.assertEqual(observation["periodStart"], "2026-04-01")
            self.assertEqual(observation["periodEnd"], "2026-06-30")
            self.assertEqual(observation["sourceSha256"], DLO["sha256"])
            self.assertEqual(observation["reviewStatus"], "needs-reconciliation" if DLO.get("revised") else "pending-review")
            self.assertTrue(observation["reviewVersionId"].startswith("review:"))
            self.assertIn(observation["sourceRaw"], [r[1] for t in DLO["tables"] for r in t["rows"] if len(r) > 1])
        self.assertEqual(result["newProposals"], 4)

    def test_same_document_replay_creates_no_new_proposals(self):
        first = self.run_extract()
        after = self.run_extract(previous=first)
        self.assertEqual(after["newProposals"], 0)
        self.assertEqual(after["observations"], first["observations"])

    def test_same_report_with_changed_sha_creates_new_proposal_versions(self):
        first = self.run_extract()
        doc = copy.deepcopy(DLO)
        doc["sha256"] = "e"*64
        doc["revised"] = True
        after = self.run_extract(doc, first)
        self.assertEqual(after["newProposals"], 4)
        self.assertEqual(len(after["observations"]), 8)
        self.assertEqual(len({o["reviewVersionId"] for o in after["observations"]}), 2)
        self.assertTrue(all(o["reviewStatus"] in ("pending-review","needs-reconciliation") for o in after["observations"]))

    def test_changed_sha_without_revised_hint_still_requires_reconciliation(self):
        first_doc = copy.deepcopy(DLO)
        first_doc["revised"] = False
        first = self.run_extract(first_doc)
        self.assertTrue(all(o["reviewStatus"] == "pending-review"
                            for o in first["observations"]))
        revised_doc = copy.deepcopy(first_doc)
        revised_doc["sha256"] = "e" * 64
        # Simulate lost collector revision metadata: digest remains authoritative.
        revised_doc["revised"] = False
        result = self.run_extract(revised_doc, first)
        self.assertEqual(result["newProposals"], 4)
        self.assertEqual(len(result["observations"]), 8)
        new = [o for o in result["observations"] if o["sourceSha256"] == "e" * 64]
        self.assertEqual(len(new), 4)
        self.assertTrue(all(o["reviewStatus"] == "needs-reconciliation" and
                            o["revisedSource"] for o in new))
        self.assertTrue(all(o["reviewStatus"] == "pending-review"
                            for o in result["observations"] if o["sourceSha256"] != "e" * 64))

    def test_reconciliation_cannot_be_downgraded_by_replayed_collector_metadata(self):
        first = self.run_extract()
        self.assertTrue(all(o["reviewStatus"] == "needs-reconciliation"
                            for o in first["observations"]))
        replay = copy.deepcopy(DLO)
        replay["revised"] = False
        second = self.run_extract(replay, first)
        self.assertEqual(second["newProposals"], 0)
        self.assertEqual(second["observations"], first["observations"])

    def test_injected_approval_in_public_data_branch_fails_closed(self):
        first = self.run_extract()
        poisoned = copy.deepcopy(first)
        poisoned["observations"][0]["reviewStatus"] = "approved"
        with self.assertRaisesRegex(ValueError, "Untrusted approval state"):
            self.run_extract(previous=poisoned)
        self.assertEqual(first["observations"][0]["reviewStatus"], "needs-reconciliation")

    def test_rejects_bogus_issuer_and_missing_headers(self):
        bad = copy.deepcopy(DLO)
        bad["companyId"] = "candidate-iren"
        self.assertEqual(self.run_extract(bad)["observations"], [])
        bad = copy.deepcopy(DLO)
        bad["tables"][0]["rows"][1][1] = "2025"
        result = self.run_extract(bad)
        self.assertFalse(any(o["metricId"] in ("revenue","grossProfit") for o in result["observations"]))
        self.assertEqual(len(result["issues"]), 2)

    def test_rejects_conflicting_and_missing_source_rows(self):
        doc = copy.deepcopy(DLO)
        r = next(r for r in doc["tables"][0]["rows"] if r[0] == "Revenue")
        doc["tables"][0]["rows"].append([r[0],"999.9"])
        result = self.run_extract(doc)
        self.assertNotIn("revenue", [o["metricId"] for o in result["observations"]])
        self.assertTrue(any(i["metricId"] == "revenue" for i in result["issues"]))

    def test_fails_on_unexpected_number_sign_or_shape(self):
        for raw in ("1,2", "1e2", "--", "", "NaN", "10 USD"):
            with self.assertRaises(ValueError):
                amount(raw)
        doc = copy.deepcopy(DLO)
        r = next(r for r in doc["tables"][1]["rows"] if r[0] == "Capital expenditures²")
        r[1] = "9,910"
        result = self.run_extract(doc)
        self.assertTrue(any(i["metricId"] == "capex" for i in result["issues"]))

    def test_rejects_a_document_with_unapproved_url_or_no_data(self):
        bad = copy.deepcopy(DLO)
        bad["url"] = "https://malicious.example/news-release/2026/08/13/3344936/0/en/dlocal-reports-second-quarter-2026-financial-results.html"
        self.assertEqual(self.run_extract(bad)["observations"], [])
        bad = copy.deepcopy(DLO)
        bad["status"] = "failed"
        self.assertEqual(self.run_extract(bad)["observations"], [])

if __name__=="__main__":
    unittest.main()
