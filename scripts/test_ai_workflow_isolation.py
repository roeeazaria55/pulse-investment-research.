"""Offline regression proving paid AI cannot ride the public Pages schedule."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class AIWorkflowIsolationTests(unittest.TestCase):
    def test_pages_pipeline_contains_no_model_execution_or_secret(self):
        pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertNotIn("OPENAI_API_KEY", pages)
        self.assertNotIn("run_optional_ai_review.py", pages)
        self.assertNotIn("ai_review:", pages)
        self.assertIn("latest_research_updates.py", pages)
        self.assertIn("pulse-data", pages)

    def test_ai_is_separate_manual_read_only_no_artifact(self):
        review = (ROOT / ".github/workflows/ai-review.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", review)
        self.assertNotIn("schedule:", review)
        self.assertNotIn("pull_request:", review)
        self.assertIn("refs/heads/main", review)
        self.assertIn("APPROVE_SINGLE_PAID_AI_REQUEST", review)
        self.assertIn("contents: read", review)
        self.assertNotIn("contents: write", review)
        self.assertNotIn("upload-artifact", review)
        runner = (ROOT / "scripts/run_optional_ai_review.py").read_text(encoding="utf-8")
        self.assertNotIn("write_text(", runner)
        self.assertNotIn("work/ai-review-", runner)
        self.assertIn("validated-in-memory", runner)

    def test_pwa_cache_is_rotated_for_new_research_shell(self):
        sw = (ROOT / "public/sw.js").read_text(encoding="utf-8")
        self.assertIn('pulse-v5-model-review-20261025', sw)


if __name__ == "__main__":
    unittest.main()
