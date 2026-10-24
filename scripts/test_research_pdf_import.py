import hashlib
import tempfile
import unittest
import zipfile
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
                with patch("import_research_pdfs.TARGET", Path(t) / "pdf"), patch("import_research_pdfs.PAGES_TARGET", Path(t) / "pages"):
                    with self.assertRaises(ValueError):
                        install(str(package), dry_run=False)
                self.assertEqual((Path(t) / "pdf" / "Source0.pdf").read_bytes(), b"different document")
        finally:
            package.unlink()


    def test_rejects_ticker_path_escape_before_any_import_write(self):
        package = ResearchBundleTests().make_bundle(
            lambda entries, blobs: entries[0].update(ticker="../escaped")
        )
        try:
            with tempfile.TemporaryDirectory() as t:
                with patch("import_research_pdfs.TARGET", Path(t) / "pdf"), patch(
                    "import_research_pdfs.PAGES_TARGET", Path(t) / "pages"
                ):
                    with self.assertRaises(ValueError):
                        install(str(package), dry_run=False)
                self.assertFalse((Path(t) / "escaped.pages.json").exists())
                self.assertFalse((Path(t) / "pdf").exists())
                self.assertFalse((Path(t) / "pages").exists())
        finally:
            package.unlink()



    def test_rejects_symlinked_pdf_even_when_contents_match(self):
        package = ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t)
                pdf = root / "pdf"
                pdf.mkdir()
                with zipfile.ZipFile(package) as archive:
                    expected = archive.read("originals/Source0.pdf")
                outside = root / "outside.pdf"
                outside.write_bytes(expected)
                (pdf / "Source0.pdf").symlink_to(outside)
                with patch("import_research_pdfs.TARGET", pdf), patch(
                    "import_research_pdfs.PAGES_TARGET", root / "pages"
                ):
                    with self.assertRaisesRegex(ValueError, "Symbolic link"):
                        install(str(package), dry_run=False)
                self.assertEqual(outside.read_bytes(), expected)
                self.assertFalse((root / "pages").exists())
        finally:
            package.unlink()

    def test_rejects_symlinked_page_text_before_any_pdf_write(self):
        package = ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t)
                pages = root / "pages"
                pages.mkdir()
                with zipfile.ZipFile(package) as archive:
                    expected = archive.read("extracted/T0.pages.json")
                outside = root / "outside.pages.json"
                outside.write_bytes(expected)
                (pages / "T0.pages.json").symlink_to(outside)
                with patch("import_research_pdfs.TARGET", root / "pdf"), patch(
                    "import_research_pdfs.PAGES_TARGET", pages
                ):
                    with self.assertRaisesRegex(ValueError, "Symbolic link"):
                        install(str(package), dry_run=False)
                self.assertEqual(outside.read_bytes(), expected)
                self.assertFalse((root / "pdf").exists())
        finally:
            package.unlink()

    def test_rejects_symlinked_output_directory(self):
        package = ResearchBundleTests().make_bundle()
        try:
            with tempfile.TemporaryDirectory() as t:
                root = Path(t)
                outside = root / "elsewhere"
                outside.mkdir()
                (root / "pdf").symlink_to(outside, target_is_directory=True)
                with patch("import_research_pdfs.TARGET", root / "pdf"), patch(
                    "import_research_pdfs.PAGES_TARGET", root / "pages"
                ):
                    with self.assertRaisesRegex(ValueError, "Symbolic link"):
                        install(str(package), dry_run=False)
                self.assertEqual(list(outside.iterdir()), [])
                self.assertFalse((root / "pages").exists())
        finally:
            package.unlink()


if __name__ == "__main__":
    unittest.main()
