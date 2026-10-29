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
  self.assertIn("public/research-release-proposals/",workflow)
  self.assertNotIn("git add -- public/approved-research/",workflow)
  self.assertNotIn("git add -- public/data/approved-research-versions.json",workflow)
  self.assertNotIn("OPENAI_API_KEY",workflow)
 def test_second_publication_and_rollback_never_bypass_owner_merge(self):
  for filename in ("research-final-publication.yml","research-rollback.yml"):
   workflow=(ROOT/".github/workflows"/filename).read_text(encoding="utf-8")
   self.assertIn("workflow_dispatch:",workflow)
   self.assertNotIn("pull_request_target:",workflow)
   self.assertIn("github.ref == 'refs/heads/main'",workflow)
   self.assertIn("vars.RESEARCH_RELEASE_PROPOSALS_ENABLED == 'YES'",workflow)
   self.assertIn("name: pulse-research-release",workflow)
   self.assertIn("python3 scripts/pulse_release_security.py",workflow)
   self.assertIn("gh pr create --draft",workflow)
   self.assertNotIn("gh pr merge",workflow)
   self.assertNotIn("git push origin HEAD:main",workflow)
   self.assertNotIn("OPENAI_API_KEY",workflow)
  publish=(ROOT/".github/workflows/research-final-publication.yml").read_text(encoding="utf-8")
  self.assertIn("--approved-index public/data/approved-research-versions.json",publish)
  self.assertIn("public/data/approved-research-versions.json",publish)
  self.assertNotIn("src/data/models/",publish)
  rollback=(ROOT/".github/workflows/research-rollback.yml").read_text(encoding="utf-8")
  self.assertIn("scripts/pulse_research_rollback.py",rollback)
  self.assertIn("public/data/research-release-audit",rollback)
 def test_github_token_uses_read_evidence_and_never_self_approves(self):
  for filename in ("research-release-proposal.yml", "research-final-publication.yml", "research-rollback.yml", "ai-automation.yml"):
   workflow=(ROOT/".github/workflows"/filename).read_text(encoding="utf-8")
   self.assertIn("actions: read",workflow)
   self.assertIn("checks: read",workflow)
   self.assertNotIn("actions: write",workflow)
   self.assertNotIn("gh pr review",workflow)
   self.assertNotIn("gh pr merge",workflow)
   self.assertNotRegex(workflow,r"--approve(?:\s|$)")
   self.assertNotIn("PULSE_SECURITY_READ_TOKEN",workflow)
  ai=(ROOT/".github/workflows/ai-automation.yml").read_text(encoding="utf-8")
  self.assertLess(ai.index("run: python3 scripts/pulse_release_security.py --environment pulse-ai-paid\n"), ai.index("--phase reserve"))
  check=(ROOT/".github/workflows/check.yml").read_text(encoding="utf-8")
  self.assertIn("ready_for_review",check)
  self.assertIn("--preflight",check)
 def test_pdf_generation_is_separate_from_actual_research_publication(self):
  release=(ROOT/"scripts/pulse_research_release.py").read_text(encoding="utf-8")
  self.assertIn("publishAutomatically",release)
  self.assertIn("False",release)
  self.assertNotIn("git push",release)
  self.assertIn("human-protected-github-pr-merge-required",release)
if __name__=="__main__":unittest.main()
