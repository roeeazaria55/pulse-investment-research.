"""Private-source import tests require no external network or PDF parser."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from manual_official_import import stage, ROOT


class ManualSourceImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.source = self.dir / "report.pdf"
        self.body = b"%PDF-1.7\n" + b"Verified-issuer-original-" * 20
        self.source.write_bytes(self.body)
        self.private = self.dir / "staging"
        self.private.mkdir()
        self.company_id = "candidate-ftai"
        self.url = "https://ftandi.gcs-web.com/node/13051/pdf"
        self.registry = json.loads((ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))
        self.previous = {"version":1,"documents":[],"sources":[],"generatedAt":"2026-10-25T10:00:00Z"}
        self.digest = hashlib.sha256(self.body).hexdigest()

    def reader(self, body, ct, url, company):
        return {"status":"extracted","sha256":hashlib.sha256(body).hexdigest(),
                "bytes":len(body),"format":"pdf","tables":[{"page":1,"rows":[["Total revenues","953,085"]]}],
                "facts":[],"reviewStatus":"pending-review","title":"FTAI Aviation Ltd. Reports Second Quarter 2026 Results",
                "links":[],"tableCount":1,"sourcePdfPages":[{"page":2,
                    "text":"FTAI AVIATION LTD. CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited) "
                      "Three Months Ended June 30 Six Months Ended June 30 "
                      "2026 2025 2026 2025 "
                      "Total revenues 953,085 676,237 1,783,782 1,178,317"}]}

    def run_stage(self, **overrides):
        args={"source":self.source,"issuer":self.company_id,"url":self.url,
              "period":"Q2 2026","published":"2026-07-29",
              "output_dir":self.private,"registry":self.registry,
              "previous":self.previous,"reader":self.reader}
        return stage(**(args|overrides))

    def test_hash_is_from_actual_pdf_and_never_from_json(self):
        result=self.run_stage()
        self.assertEqual(result["sha256"],self.digest)
        self.assertEqual(Path(result["pdf"]).read_bytes(),self.body)
        snapshot=json.loads(Path(result["stagedFeed"]).read_text(encoding="utf-8"))
        report=snapshot["documents"][0]
        self.assertEqual(report["sha256"],self.digest)
        self.assertEqual(report["url"],self.url)
        self.assertEqual(report["reviewStatus"],"pending-review")
        self.assertEqual(result["numberOfReviewedMetricCandidates"],1)
        self.assertEqual(report["provenance"],"manually-downloaded-original-pdf-human-verification-required")
        self.assertEqual(snapshot["sources"][0]["status"],"deferred")
        manifest=json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertFalse(manifest["pdfArchivedPublicly"])
        self.assertTrue(manifest["identityReviewRequired"])
        self.assertEqual(manifest["originalPdfSha256"],self.digest)
        self.assertFalse(Path(result["pdf"]).stat().st_mode & 0o077)
        with self.assertRaisesRegex(ValueError,"overwrite"):
            self.run_stage()

    def test_rejects_unofficial_issuer_url_and_incorrect_identity(self):
        with self.assertRaisesRegex(ValueError,"official issuer"):
            self.run_stage(url="https://hostile.invalid/ftai.pdf")
        with self.assertRaisesRegex(ValueError,"registered company"):
            self.run_stage(issuer="candidate-unknown")

    def test_rejects_corrupt_pdf_and_unverified_extractor(self):
        self.source.write_bytes(b"Not really a PDF"+b"x"*200)
        with self.assertRaisesRegex(ValueError,"not a PDF"):
            self.run_stage()
        self.source.write_bytes(self.body)
        bad_reader=lambda *args: {**self.reader(*args),"sha256":"a"*64}
        with self.assertRaisesRegex(ValueError,"digest"):
            self.run_stage(reader=bad_reader)
        bad_reader=lambda *args: {**self.reader(*args),"tables":[],"sourcePdfPages":[]}
        with self.assertRaisesRegex(ValueError,"source-row"):
            self.run_stage(reader=bad_reader)

    def test_rejects_private_staging_inside_public_repository(self):
        with self.assertRaisesRegex(ValueError,"outside"):
            self.run_stage(output_dir=ROOT / "scripts")

    def test_unrecognized_dates_and_document_version_never_overwrite(self):
        with self.assertRaisesRegex(ValueError,"publication"):
            self.run_stage(published="2026-17-40")
        report={"id":"report:"+hashlib.sha256((self.company_id+"|"+self.url).encode()).hexdigest()[:32],
                "sha256":"f"*64,"firstDetectedAt":"2026-08-01T08:00:00Z",
                "lastSuccessfulAt":"2026-08-01T08:00:00Z","revisions":[]}
        prior={**self.previous,"documents":[report]}
        result=self.run_stage(previous=prior)
        copied=json.loads(Path(result["stagedFeed"]).read_text(encoding="utf-8"))["documents"][0]
        self.assertTrue(copied["revised"])
        self.assertEqual(copied["revisions"][0]["sha256"],"f"*64)


if __name__=="__main__":
    unittest.main()
