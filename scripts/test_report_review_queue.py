"""No fabricated financial figures: review-queue tests use synthetic hashes only."""
import copy
import json
import unittest
from pathlib import Path

from report_review_queue import build_queue, version_id, report_id

NOW = "2026-10-22T12:00:00+00:00"
LATER = "2026-10-22T13:00:00+00:00"
COMPANY = {"id": "candidate-nebius", "ticker": "NBIS", "allowedHosts": ["nebius.com"], "documentPaths": ["/newsroom/"]}
REGISTRY = {"companies": [COMPANY]}
URL = "https://nebius.com/newsroom/test-results"
DOC = {
    "id": report_id(COMPANY["id"], URL),
    "companyId": COMPANY["id"], "ticker": "NBIS", "url": URL,
    "sha256": "a" * 64, "status": "extracted",
    "lastSuccessfulAt": NOW, "publishedDate": "2026-08-01",
    "documentPeriod": None, "parserVersion": "official-content-v1",
    "tableCount": 4, "facts": [{"concept": "source-only"}],
    "revised": False, "revisions": [], "error": None,
}
SNAPSHOT = {"version": 1, "generatedAt": NOW, "documents": [DOC], "sources": []}


class ReportReviewQueueTests(unittest.TestCase):
    def collect(self, snapshot=None, previous=None, now=NOW):
        return build_queue(snapshot if snapshot is not None else SNAPSHOT,
                           REGISTRY, previous or {}, now)

    def test_new_document_creates_one_pending_review_not_a_financial_mapping(self):
        result = self.collect()
        self.assertEqual(result["summary"]["newPendingVersions"], 1)
        entry = result["entries"][0]
        self.assertEqual(entry["id"], version_id(COMPANY["id"], DOC["id"], DOC["sha256"]))
        self.assertEqual(entry["reviewStatus"], "pending-review")
        self.assertTrue(entry["currentVersion"])
        self.assertEqual(entry["sourceUrl"], URL)
        self.assertEqual(entry["structuredFactCount"], 1)
        self.assertEqual(entry["periodReview"], "unverified-source-metadata")
        self.assertNotIn("targetPrice", entry)
        self.assertNotIn("financialMetrics", entry)

    def test_same_report_and_hash_is_idempotent_and_preserves_first_seen(self):
        first = self.collect()
        second = self.collect(previous=first, now=LATER)
        self.assertEqual(len(second["entries"]), 1)
        self.assertEqual(second["summary"]["newPendingVersions"], 0)
        self.assertEqual(second["entries"][0]["firstObservedAt"], NOW)
        self.assertEqual(second["entries"][0]["lastSeenAt"], LATER)

    def test_new_hash_for_same_report_is_a_new_pending_version_with_history(self):
        first = self.collect()
        revised = copy.deepcopy(SNAPSHOT)
        revised["documents"][0].update(sha256="b" * 64, revised=True,
                                        lastSuccessfulAt=LATER)
        result = self.collect(revised, first, LATER)
        self.assertEqual(result["summary"]["newPendingVersions"], 1)
        self.assertEqual(result["summary"]["newRevisedVersions"], 1)
        self.assertEqual(len(result["entries"]), 2)
        current = [e for e in result["entries"] if e["currentVersion"]]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["sha256"], "b" * 64)
        self.assertTrue(all(e["reviewStatus"] == "pending-review" for e in result["entries"]))

    def test_failed_refresh_keeps_previous_evidence_and_does_not_invent_report(self):
        old = self.collect()
        failed = copy.deepcopy(SNAPSHOT)
        failed["documents"] = []
        failed["sources"] = [{"companyId": COMPANY["id"], "status": "failed", "error": "HTTP 403"}]
        result = self.collect(failed, old, LATER)
        self.assertEqual(len(result["entries"]), 1)
        self.assertFalse(result["entries"][0]["currentVersion"])
        self.assertEqual(result["summary"]["newPendingVersions"], 0)
        self.assertEqual(result["failures"][0]["error"], "HTTP 403")
        self.assertIn("does not mean no report", result["notice"])

    def test_document_with_last_known_data_and_failed_refresh_preserves_current_version(self):
        old = self.collect()
        failed = copy.deepcopy(SNAPSHOT)
        failed["documents"][0]["error"] = "HTTP 403"
        failed["sources"] = [{"companyId": COMPANY["id"], "status": "failed", "error": "HTTP 403"}]
        result = self.collect(failed, old, LATER)
        self.assertTrue(result["entries"][0]["currentVersion"])
        self.assertEqual(result["entries"][0]["refreshError"], "HTTP 403")
        self.assertEqual(result["summary"]["newPendingVersions"], 0)

    def test_rejects_incomplete_or_untrusted_document_evidence(self):
        snapshot = copy.deepcopy(SNAPSHOT)
        bad = [
            {**DOC, "sha256": "not-a-hash"},
            {**DOC, "url": "http://nebius.com/newsroom/test-results"},
            {**DOC, "url": "https://evil.example/newsroom/test-results"},
            {**DOC, "status": "failed"},
            {**DOC, "companyId": "unknown"},
            {**DOC, "lastSuccessfulAt": "nonsense"},
        ]
        snapshot["documents"] = bad
        result = self.collect(snapshot)
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["summary"]["invalidDocuments"], len(bad))

    def test_rejects_forged_report_identity_for_current_source(self):
        forged = copy.deepcopy(SNAPSHOT)
        forged["documents"][0]["id"] = "report:" + "0" * 32
        result = self.collect(forged)
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["summary"]["invalidDocuments"], 1)
        changed_url = copy.deepcopy(SNAPSHOT)
        changed_url["documents"][0]["url"] = URL + "-different"
        result = self.collect(changed_url)
        self.assertEqual(result["summary"]["invalidDocuments"], 1)

    def test_rejects_forged_or_duplicate_prior_pending_versions(self):
        first = self.collect()
        for field, forged_value in [("id", "review:" + "0" * 32),
                                    ("reportId", "report:" + "0" * 32),
                                    ("sha256", "b" * 64),
                                    ("sourceUrl", URL + "-other")]:
            corrupted = copy.deepcopy(first)
            corrupted["entries"][0][field] = forged_value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Untrusted"):
                self.collect(previous=corrupted, now=LATER)
        duplicated = copy.deepcopy(first)
        duplicated["entries"].append(copy.deepcopy(duplicated["entries"][0]))
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.collect(previous=duplicated, now=LATER)

    def test_real_saved_queue_and_intake_replay_without_losing_versions(self):
        root = Path("public/data")
        registry = json.loads((root / "official-registry.json").read_text())
        intake = json.loads((root / "report-intake.json").read_text())
        saved = json.loads((root / "report-review-queue.json").read_text())
        replay = build_queue(intake, registry, saved, "2026-10-24T00:00:00+00:00")
        self.assertGreaterEqual(len(replay["entries"]), len(saved["entries"]))
        self.assertTrue(all(e["reviewStatus"] == "pending-review" for e in replay["entries"]))

    def test_preserves_existing_pending_records_without_auto_approval(self):
        first = self.collect()
        first["entries"][0]["reviewStatus"] = "approved"
        result = self.collect(previous=first, now=LATER)
        self.assertEqual(result["entries"][0]["reviewStatus"], "pending-review")
        self.assertEqual(result["summary"]["newPendingVersions"], 1)

    def test_rejects_invalid_snapshot_without_mutating_previous(self):
        first = self.collect()
        original = copy.deepcopy(first)
        with self.assertRaises(ValueError):
            self.collect({"version": 0, "documents": []}, first)
        self.assertEqual(first, original)


if __name__ == "__main__":
    unittest.main()
