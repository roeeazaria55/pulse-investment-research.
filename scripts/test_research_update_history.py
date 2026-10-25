"""Public history: identical report never duplicates and revised source never erases old work."""
import copy
import unittest
from research_update_history import combine, MAX_PER_ISSUER


class ResearchHistoryTests(unittest.TestCase):
    def report(self, content_id="a"*24, company="us-dlo-nasdaq-a"):
        return {"companyId": company, "ticker": "DLO", "contentId": content_id,
                "status": "needs-reconciliation", "reportPeriod": "Q2 2026",
                "publishedDate": "2026-08-13", "sourceVersion": "b"*64,
                "metrics": [{"id": "revenue", "value": 399.7}],
                "reviewRequired": True, "aiAnalysisEnabled": False}
    def snapshot(self, reports=None, at="2026-10-25T08:00:00+00:00"):
        return {"version": 1, "generatedAt": at, "reports": reports or []}

    def test_first_run_retains_full_issuer_report(self):
        h, n = combine(None, self.snapshot([self.report()]))
        self.assertEqual(n, 1)
        self.assertEqual(h["entries"][0]["report"]["metrics"][0]["value"], 399.7)
        self.assertEqual(h["entries"][0]["firstSeenAt"], "2026-10-25T08:00:00+00:00")

    def test_rerun_does_not_create_false_new_update(self):
        h, n = combine(None, self.snapshot([self.report()]))
        again, added = combine(h, self.snapshot([self.report()], at="2026-10-26T08:00:00+00:00"))
        self.assertEqual(added, 0)
        self.assertEqual(h, again)
        self.assertEqual(len(again["entries"]), 1)

    def test_report_revision_preserves_prior_version(self):
        original, _ = combine(None, self.snapshot([self.report()]))
        changed = self.report("c"*24)
        changed["metrics"][0]["value"] = 410
        updated, added = combine(original, self.snapshot([changed], at="2026-10-27T08:00:00Z"))
        self.assertEqual(added, 1)
        self.assertEqual(len(updated["entries"]), 2)
        self.assertEqual([e["report"]["metrics"][0]["value"] for e in updated["entries"]], [399.7, 410])

    def test_stale_id_with_changed_payload_fails_closed(self):
        original, _ = combine(None, self.snapshot([self.report()]))
        tampered = self.report()
        tampered["metrics"][0]["value"] = 9000
        with self.assertRaisesRegex(ValueError, "without a version"):
            combine(original, self.snapshot([tampered]))

    def test_unreviewed_evidence_never_enters_archive(self):
        report = self.report()
        report["reviewRequired"] = False
        with self.assertRaisesRegex(ValueError, "Non-review"):
            combine(None, self.snapshot([report]))

    def test_missing_data_never_erases_previous_good_history(self):
        original, _ = combine(None, self.snapshot([self.report()]))
        no_data = self.report()
        no_data["metrics"] = []
        no_data["contentId"] = None
        after, n = combine(original, self.snapshot([no_data], "2026-10-26T08:00:00Z"))
        self.assertEqual(n, 0)
        self.assertEqual(after, original)

    def test_duplicate_saved_entry_rejected(self):
        original, _ = combine(None, self.snapshot([self.report()]))
        bad = copy.deepcopy(original)
        bad["entries"].append(copy.deepcopy(bad["entries"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            combine(bad, self.snapshot())

    def test_bounded_history(self):
        old = None
        for i in range(MAX_PER_ISSUER + 3):
            item = self.report(f"{i:024x}")
            old, _ = combine(old, self.snapshot([item], at=f"2026-10-{i+10:02d}T08:00:00Z"))
        self.assertEqual(len(old["entries"]), MAX_PER_ISSUER)
        self.assertEqual(old["entries"][-1]["contentId"], f"{MAX_PER_ISSUER+2:024x}")


if __name__ == "__main__":
    unittest.main()
