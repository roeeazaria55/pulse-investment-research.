"""Read-only CI regression guardrails for PULSE publication boundaries.

These tests detect accidental workflow edits. They do NOT enforce GitHub
branch protection or authenticate analyst reviewers.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / ".github/workflows/pages.yml"
CHECK = ROOT / ".github/workflows/check.yml"
NOTIFY = ROOT / ".github/workflows/notify.yml"


def job(source, name):
    match = re.search(r"(?m)^  " + re.escape(name) + r":\s*$", source)
    if match is None:
        raise AssertionError("Missing required workflow job: " + name)
    remaining = source[match.end():]
    next_job = re.search(r"(?m)^  [a-z][a-z-]*:\s*$", remaining)
    return remaining[:next_job.start()] if next_job else remaining


class PipelineIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = PAGES.read_text(encoding="utf-8")
        cls.check = CHECK.read_text(encoding="utf-8")
        cls.notify = NOTIFY.read_text(encoding="utf-8")

    def test_collector_executes_main_code_and_reads_separate_data_history(self):
        collect = job(self.pages, "collect")
        self.assertIn("ref: main", collect)
        self.assertIn("persist-credentials: false", collect)
        self.assertIn("contents: read", collect)
        self.assertIn("git fetch --no-tags origin refs/heads/pulse-data:", collect)
        self.assertIn('git show "refs/remotes/origin/pulse-data:$file"', collect)
        self.assertIn('echo "sha=$(git rev-parse HEAD)"', collect)
        self.assertIn("npm run build", collect)
        self.assertIn("actions/upload-pages-artifact@v3", collect)
        self.assertNotIn("contents: write", collect)
        self.assertNotRegex(collect, r"(?m)^\s*(?:git push|git add|gh pr merge)\b")

    def test_only_public_snapshot_files_are_committed_to_pulse_data(self):
        persist = job(self.pages, "persist")
        self.assertIn("ref: pulse-data", persist)
        self.assertIn("contents: write", persist)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXPECTED_BASE"', persist)
        self.assertIn("git push origin HEAD:pulse-data", persist)
        lines = [line.strip() for line in persist.splitlines() if line.strip().startswith("git add -- ")]
        self.assertEqual(len(lines), 1, "Only one allowlisted staging command is permitted")
        files = lines[0].removeprefix("git add -- ").split()
        self.assertGreaterEqual(len(files), 7)
        self.assertTrue(all(name.startswith("public/data/") for name in files))
        self.assertTrue(all(".." not in name and not any(ch in name for ch in "*?[]") for name in files))
        self.assertIn("public/data/auto-financial-observations.json", files)
        self.assertIn("public/data/forecast-archive.json", files)
        self.assertNotIn("ref: main", persist)
        self.assertNotIn("git add -A", persist)
        self.assertNotIn("git add .", persist)

    def test_pages_deploy_requires_exact_code_and_persisted_data_commit(self):
        deploy = job(self.pages, "deploy")
        self.assertIn("needs: [collect, persist]", deploy)
        self.assertIn("EXPECTED_HEAD: ${{ needs.collect.outputs.base_sha }}", deploy)
        self.assertIn("EXPECTED_DATA_HEAD: ${{ needs.persist.outputs.sha }}", deploy)
        self.assertIn("ref:'heads/main'", deploy)
        self.assertIn("ref:'heads/pulse-data'", deploy)
        self.assertIn("data.object.sha !== process.env.EXPECTED_HEAD", deploy)
        self.assertIn("state.data.object.sha !== process.env.EXPECTED_DATA_HEAD", deploy)
        self.assertIn("actions/deploy-pages@v4", deploy)
        self.assertNotIn("git push", deploy)

    def test_notifications_only_follow_successful_deployment(self):
        notify = job(self.pages, "notify")
        self.assertIn("needs: deploy", notify)
        self.assertIn("if: success()", notify)
        self.assertIn("uses: ./.github/workflows/notify.yml", notify)
        self.assertIn("contents: read", notify)
        private = job(self.notify, "notify")
        self.assertIn("ref: main", private)
        self.assertIn("persist-credentials: false", private)
        self.assertIn("Use the exact published public snapshot", private)
        self.assertIn("actions/cache/restore@v4", private)
        self.assertIn("actions/cache/save@v4", private)
        self.assertIn("One transport attempt per persisted intent", private)

    def test_pull_request_checks_never_receive_write_permissions(self):
        self.assertIn("pull_request:", self.check)
        self.assertIn("permissions:\n  contents: read", self.check)
        self.assertIn("persist-credentials: false", self.check)
        self.assertNotIn("contents: write", self.check)
        self.assertNotIn("pull_request_target:", self.check)
        self.assertNotRegex(self.check, r"(?m)^\s*(?:git push|gh pr merge)\b")

    def test_no_workflow_force_push_or_main_write_path(self):
        for workflow in (self.pages, self.check, self.notify):
            self.assertNotRegex(workflow, r"(?m)^\s*git push\s+.*(?:HEAD:main|origin main|--force)")
            self.assertNotIn("pull_request_target:", workflow)
        self.assertIn("git push origin HEAD:pulse-data", self.pages)
        self.assertNotIn("git push origin HEAD:main", self.pages)


if __name__ == "__main__":
    unittest.main()
