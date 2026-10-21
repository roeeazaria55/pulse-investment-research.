import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_research_bundle import ResearchBundleTests
from import_research_pdfs import install


class ResearchPdfImportTests(unittest.TestCase):
    def test_dry_run_then_explicit_apply_and_idempotence(self):
        package = ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as t:
                with patch("import_research_pdfs.TARGET", Path(t) / "pdf"), patch("import_research_pdfs.PAGES_TARGET", Path(t) / "pages"):
                    self.assertEqual(len(install(str(package))), 14)
                    self.assertFalse((Path(t) / "pdf" / "Source0.pdf").exists())
                    self.assertEqual(len(install(str(package), dry_run=False)), 14)
                    self.assertEqual(install(str(package), dry_run=False), [])
                    self.assertTrue((Path(t) / "pdf" / "Source0.pdf").read_bytes().startswith(b"%PDF"))
                    self.assertTrue((Path(t) / "pages" / "T0.pages.json").exists())
        finally:
            package.unlink()

    def test_refuses_conflicting_existing_pdf(self):
        package = ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as t:
                (Path(t) / "pdf").mkdir()
                (Path(t) / "pdf" / "Source0.pdf").write_bytes(b"different document")
                with patch("import_research_pdfs.TARGET", Path(t)):
                    with self.assertRaises(ValueError):
                        install(str(package), dry_run=False)
                self.assertEqual((Path(t) / "pdf" / "Source0.pdf").read_bytes(), b"different document")
        finally:
            package.unlink()


if __name__ == "__main__":
    unittest.main()
