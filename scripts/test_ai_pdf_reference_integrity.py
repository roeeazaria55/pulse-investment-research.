"""Offline guards for untrusted supplied PDF pointers in AI input packets."""
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class SuppliedPdfPointerIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = packets.read_json(packets.ROOT / "public/data/official-registry.json")
        cls.companies = {row["ticker"]: row for row in registry["companies"]}
        supplied = packets.read_json(packets.ROOT / "src/data/suppliedResearch.json")
        cls.supplied = supplied
        cls.dlo = next(row for row in supplied if row["ticker"] == "DLO")

    def test_existing_pdfs_are_bound_to_declared_sha_and_remain_unverified(self):
        built = packets.build_all()
        for ticker in ("DLO", "NBIS", "SMCI"):
            pointer = built[ticker]["legacyResearchPdf"]
            declared = next(row for row in self.supplied if row["ticker"] == ticker)
            with self.subTest(ticker=ticker):
                self.assertEqual(pointer["availability"], "repository")
                self.assertEqual(pointer["sourceFile"]["sha256"], declared["sha256"])
                self.assertEqual(pointer["reviewStatus"], "unverified-supplied-analyst-research")
                self.assertNotIn("approved", pointer)
        self.assertIsNone(built["IREN"]["legacyResearchPdf"])

    def test_duplicate_and_cross_issuer_pdf_registry_entries_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            packets.pdf_reference(self.companies["DLO"], [self.dlo, copy.deepcopy(self.dlo)])
        for changed in (
            {**self.dlo, "companyId": self.companies["NBIS"]["id"]},
            {**self.dlo, "ticker": "NBIS"},
        ):
            with self.subTest(changed=changed["ticker"]):
                with self.assertRaisesRegex(ValueError, "Cross-issuer"):
                    packets.pdf_reference(self.companies["DLO"], [changed])

    def test_invalid_names_and_digests_are_not_silently_ignored(self):
        for filename in (
            "../escape.pdf", ".hidden.pdf", "bad..pdf", "nested/file.pdf",
            "nested\\file.pdf", "bad.pdf\n", "bad%2fpath.pdf",
            "bad.txt", "a" * 190 + ".pdf",
        ):
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(ValueError, "Malformed"):
                    packets.pdf_reference(self.companies["DLO"],
                                          [{**self.dlo, "filename": filename}])
        for digest in ("invalid", "A" * 64, None, 123):
            with self.subTest(digest=digest):
                with self.assertRaisesRegex(ValueError, "Malformed"):
                    packets.pdf_reference(self.companies["DLO"],
                                          [{**self.dlo, "sha256": digest}])

    def test_present_pdf_must_match_declared_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "public/research"
            folder.mkdir(parents=True)
            payload = b"%PDF-1.4\ncontrolled test PDF bytes"
            (folder / self.dlo["filename"]).write_bytes(payload)
            with patch.object(packets, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    packets.pdf_reference(self.companies["DLO"], [self.dlo])
                valid = {**self.dlo, "sha256": hashlib.sha256(payload).hexdigest()}
                pointer = packets.pdf_reference(self.companies["DLO"], [valid])
                self.assertEqual(pointer["sourceFile"]["sha256"], valid["sha256"])
                self.assertEqual(pointer["availability"], "repository")

    def test_missing_pdf_is_unavailable_but_not_approved(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(packets, "ROOT", Path(temp)):
                pointer = packets.pdf_reference(self.companies["DLO"], [self.dlo])
        self.assertEqual(pointer["availability"], "unavailable")
        self.assertIsNone(pointer["sourceFile"])
        self.assertEqual(pointer["reviewStatus"], "unverified-supplied-analyst-research")

    def test_symlink_file_and_directory_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "public/research"
            folder.mkdir(parents=True)
            outside = root / "outside.pdf"
            outside.write_bytes(b"%PDF-1.4\nnot an approved source")
            (folder / self.dlo["filename"]).symlink_to(outside)
            with patch.object(packets, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    packets.pdf_reference(self.companies["DLO"], [self.dlo])
            (folder / self.dlo["filename"]).unlink()
            folder.rmdir()
            folder.symlink_to(root, target_is_directory=True)
            with patch.object(packets, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    packets.pdf_reference(self.companies["DLO"], [self.dlo])


if __name__ == "__main__":
    unittest.main()
