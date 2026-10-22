"""Guardrails for separating continuously refreshed public state from reviewed main."""
import unittest
from pathlib import Path

WORKFLOW = (Path(".github/workflows/pages.yml")).read_text()


class PublicStateIsolationWorkflowTests(unittest.TestCase):
    def test_collector_reads_prior_state_from_data_branch(self):
        self.assertIn("refs/heads/pulse-data:refs/remotes/origin/pulse-data", WORKFLOW)
        self.assertIn('git show "refs/remotes/origin/pulse-data:$file" > "$file"', WORKFLOW)
        self.assertIn("data_base_sha: ${{ steps.seed.outputs.sha }}", WORKFLOW)

    def test_publisher_must_not_push_to_reviewed_main(self):
        self.assertIn("git push origin HEAD:pulse-data", WORKFLOW)
        self.assertNotIn("git push origin HEAD:main", WORKFLOW)
        self.assertIn("EXPECTED_BASE: ${{ needs.collect.outputs.data_base_sha }}", WORKFLOW)
        self.assertIn("ref: pulse-data", WORKFLOW)

    def test_deployment_rejects_superseded_code_or_data_state(self):
        self.assertIn("EXPECTED_HEAD: ${{ needs.collect.outputs.base_sha }}", WORKFLOW)
        self.assertIn("EXPECTED_DATA_HEAD: ${{ needs.persist.outputs.sha }}", WORKFLOW)
        self.assertIn("ref:'heads/main'", WORKFLOW)
        self.assertIn("ref:'heads/pulse-data'", WORKFLOW)
        self.assertIn("ref: ${{ needs.collect.outputs.base_sha }}", WORKFLOW)

    def test_existing_report_outputs_still_persist(self):
        for name in ("report-intake", "report-review-queue", "auto-financial-observations",
                     "forecast-archive", "forecast-actual-comparisons"):
            self.assertIn("public/data/"+name+".json", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
