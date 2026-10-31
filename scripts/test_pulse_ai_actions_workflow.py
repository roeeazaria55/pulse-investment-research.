"""Static security contract for pre-API workflow wiring (offline only)."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

class AIActionsContractTests(unittest.TestCase):
 def test_paid_is_not_triggered_by_pull_requests_or_pages_collection(self):
  paid=(ROOT/".github/workflows/ai-automation.yml").read_text(encoding="utf-8")
  pages=(ROOT/".github/workflows/pages.yml").read_text(encoding="utf-8")
  self.assertIn("workflow_dispatch:",paid)
  self.assertIn("schedule:",paid)
  self.assertNotIn("pull_request:",paid)
  self.assertIn("github.ref == 'refs/heads/main'",paid)
  self.assertIn("vars.PAID_AI_ENABLED == 'YES'",paid)
  self.assertIn("environment:",paid)
  self.assertIn("github.event_name == 'schedule' && 'pulse-ai-drafts' || 'pulse-ai-paid'",paid)
  self.assertIn('python3 scripts/pulse_ai_autonomous_security.py',paid)
  self.assertIn("cancel-in-progress: false",paid)
  self.assertIn("precommit",paid.lower())
  self.assertIn("git push origin HEAD:pulse-data",paid)
  self.assertIn("--reservation-precommitted",paid)
  self.assertIn("secrets.OPENAI_API_KEY",paid)
  self.assertNotIn("OPENAI_API_KEY",pages)
  self.assertNotIn("pulse_ai_actions.py",pages)
  self.assertNotIn("run_optional_ai_review.py",pages)
 def test_pulse_data_keeps_queue_and_preserves_previous_ai_drafts(self):
  pages=(ROOT/".github/workflows/pages.yml").read_text(encoding="utf-8")
  self.assertIn("scripts/pulse_ai_analysis_queue.py",pages)
  self.assertIn("public/data/ai-analysis-queue.json",pages)
  self.assertIn("public/data/ai-research-drafts.json",pages)
  self.assertIn("public/data/ai-analysis-queue.json",pages.split("git add --")[-1])
 def test_pr_check_never_requests_a_secret(self):
  checks=(ROOT/".github/workflows/check.yml").read_text(encoding="utf-8")
  self.assertIn("pulse_ai_pipeline.py --ticker META",checks)
  self.assertNotIn("secrets.OPENAI_API_KEY",checks)
  self.assertNotIn("PULSE_PAID_AI_APPROVED=YES",checks)

if __name__=="__main__":unittest.main()
