import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from validate_research_bundle import validate_bundle


class ResearchBundleTests(unittest.TestCase):
    def make_bundle(self, change=None):
        entries = []
        blobs = {}
        for i in range(7):
            original = ("%PDF-1.4\nsource%d" % i).encode()
            name = "Source%d.pdf" % i
            textname = "extracted/T%d.pages.json" % i
            entry = {
                "companyId": "company-%d" % i, "filename": name,
                "sha256": hashlib.sha256(original).hexdigest(),
                "bytes": len(original), "pages": 1,
                "extractedTextFilename": textname,
            }
            entries.append(entry)
            blobs["originals/" + name] = original
            blobs[textname] = json.dumps({"pages": [{"page": 1, "text": "source content"}]}).encode()
        if change:
            change(entries, blobs)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            path = Path(f.name)
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("manifest.json", json.dumps({"version": 1, "research": entries}))
            for name, data in blobs.items():
                z.writestr(name, data)
        return path

    def test_valid_bundle(self):
        path = self.make_bundle()
        try:
            self.assertEqual(validate_bundle(path), 7)
        finally:
            path.unlink()

    def test_tampered_pdf_fails(self):
        def tamper(entries, blobs):
            blobs["originals/Source0.pdf"] = b"%PDF-1.4\nmodified"
        path = self.make_bundle(tamper)
        try:
            with self.assertRaises(ValueError):
                validate_bundle(path)
        finally:
            path.unlink()

    def test_missing_page_text_fails(self):
        def empty(entries, blobs):
            blobs["extracted/T0.pages.json"] = json.dumps({"pages": [{"page": 1, "text": ""}]}).encode()
        path = self.make_bundle(empty)
        try:
            with self.assertRaises(ValueError):
                validate_bundle(path)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
