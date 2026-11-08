"""Non-destructive and fail-closed checks for manual research staging."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage_research_bundle import stage_bundle
from test_research_bundle import ResearchBundleTests


class ResearchStagingSafetyTests(unittest.TestCase):
    def setUp(self):
        self.bundle = ResearchBundleTests().make_bundle()

    def tearDown(self):
        self.bundle.unlink(missing_ok=True)

    def test_existing_directory_and_manifest_are_never_replaced(self):
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "staged"
            destination.mkdir()
            original = destination / "manifest.json"
            original.write_text("keep existing review", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                stage_bundle(str(self.bundle), str(destination))
            self.assertEqual(original.read_text(encoding="utf-8"), "keep existing review")
            self.assertEqual(sorted(p.name for p in destination.iterdir()), ["manifest.json"])

    def test_existing_file_and_broken_symlink_are_not_replaced(self):
        with tempfile.TemporaryDirectory() as parent:
            file_destination = Path(parent) / "staged"
            file_destination.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                stage_bundle(str(self.bundle), str(file_destination))
            self.assertEqual(file_destination.read_text(encoding="utf-8"), "keep")

            link = Path(parent) / "broken"
            link.symlink_to(Path(parent) / "missing")
            with self.assertRaises(ValueError):
                stage_bundle(str(self.bundle), str(link))
            self.assertTrue(link.is_symlink())

    def test_repository_root_and_reviewed_directories_are_forbidden(self):
        repo = Path(__file__).resolve().parent.parent
        for destination in (repo, repo / "docs" / "staging-test", repo / "public" / "staging-test"):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(ValueError, "restricted to work"):
                    stage_bundle(str(self.bundle), str(destination))
                if destination != repo:
                    self.assertFalse(destination.exists())

    def test_failed_publish_cleans_temporary_files_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "staged"
            with patch.object(Path, "rename", side_effect=OSError("simulated rename failure")):
                with self.assertRaisesRegex(OSError, "simulated"):
                    stage_bundle(str(self.bundle), str(destination))
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_new_destination_contains_only_validated_archive_files(self):
        with tempfile.TemporaryDirectory() as parent:
            destination = Path(parent) / "staged"
            self.assertEqual(stage_bundle(str(self.bundle), str(destination)), 7)
            self.assertTrue((destination / "manifest.json").is_file())
            self.assertTrue((destination / "originals" / "Source0.pdf").is_file())
            self.assertTrue((destination / "extracted" / "T0.pages.json").is_file())
            with self.assertRaises(ValueError):
                stage_bundle(str(self.bundle), str(destination))


if __name__ == "__main__":
    unittest.main()
