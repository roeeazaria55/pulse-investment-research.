"""Workflow-level publication security contract, without GitHub writes."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class ResearchProposalWorkflowChecks(unittest.TestCase):
 def test_proposal_can_only_be_started_by_enabled_protected_main_action(self):
  workflow=(ROOT/".github/workflows/research-release-proposal.yml").read_text(encoding="utf-8")
  self.assertIn("workflow_dispatch:",workflow)
  self.assertNotIn("pull_request_target:",workflow)
  self.assertNotIn("pull_request:",workflow)
  self.assertIn("github.ref == 'refs/heads/main'",workflow)
  self.assertIn("vars.RESEARCH_RELEASE_PROPOSALS_ENABLED == 'YES'",workflow)
  self.assertIn("name: pulse-research-release",workflow)
  self.assertIn("python3 scripts/pulse_release_security.py",workflow)
  self.assertLess(workflow.index("python3 scripts/pulse_release_security.py"),
                  workflow.index("gh pr create"))
  self.assertIn("gh pr create --draft",workflow)
  self.assertIn("--base main",workflow)
  self.assertNotIn("gh pr merge",workflow)
  self.assertNotIn("git push origin HEAD:main",workflow)
 def test_only_unapproved_staged_versions_are_written_to_draft_pr(self):
  workflow=(ROOT/".github/workflows/research-release-proposal.yml").read_text(encoding="utf-8")
  self.assertIn("public/data/research-release-proposals/",workflow)
  self.assertIn("public/approved-research/",workflow)
  self.assertNotIn("git add -- public/data/approved-research-versions.json",workflow)
  self.assertNotIn("OPENAI_API_KEY",workflow)
 def test_pdf_generation_is_separate_from_actual_research_publication(self):
  release=(ROOT/"scripts/pulse_research_release.py").read_text(encoding="utf-8")
  self.assertIn("publishAutomatically",release)
  self.assertIn("False",release)
  self.assertNotIn("git push",release)
  self.assertIn("human-protected-github-pr-merge-required",release)
if __name__=="__main__":unittest.main()
