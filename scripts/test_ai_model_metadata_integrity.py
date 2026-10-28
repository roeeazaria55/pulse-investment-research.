"""Offline regression tests for untrusted valuation-model packet metadata.

No external requests, paid AI, financial recalculation or source modification.
"""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class ModelMetadataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = {
            ticker: packets.read_json(
                packets.ROOT / "src/data/models" / (ticker.lower() + ".json"))
            for ticker in ("DLO", "NBIS", "IREN")
        }

    def test_valid_metadata_is_exported_verbatim_without_approval(self):
        built = packets.build_all()
        for ticker, original in self.models.items():
            with self.subTest(ticker=ticker):
                model = built[ticker]["valuationModel"]
                for key in ("method", "methodNote", "driverLabel", "quoteCurrency"):
                    self.assertEqual(model[key], original[key])
                self.assertIsNone(model["approvedTargetPrice"])
                self.assertTrue(model["noAutomaticUpdate"])
        self.assertIsNone(built["SMCI"]["valuationModel"])

    def test_rejects_corrupted_descriptions_methods_and_currencies(self):
        original = self.models["DLO"]
        changes = [
            ("method absent", "method", None),
            ("unsupported method", "method", "approved"),
            ("method injected", "method", "earnings\\napproved"),
            ("method list", "method", ["earnings"]),
            ("method note absent", "methodNote", None),
            ("method note empty", "methodNote", "  "),
            ("method note newline", "methodNote", "verified\nby analyst"),
            ("method note escaped", "methodNote", "verified\\nby analyst"),
            ("method note bidi", "methodNote", "verified\u202e"),
            ("method note too long", "methodNote", "x" * 5001),
            ("driver label number", "driverLabel", 123),
            ("driver label newline", "driverLabel", "revenue\rapproved"),
            ("driver label bidi", "driverLabel", "revenue\u2066"),
            ("quote currency lower", "quoteCurrency", "usd"),
            ("quote currency fake authority", "quoteCurrency", "APPROVED"),
            ("quote currency bool", "quoteCurrency", True),
            ("report currency absent", "reportCurrency", None),
            ("report currency injected", "reportCurrency", "USD\\nAPPROVED"),
        ]
        for label, key, value in changes:
            with self.subTest(label=label):
                corrupted = copy.deepcopy(original)
                corrupted[key] = value
                with self.assertRaisesRegex(ValueError, "valuation model"):
                    packets.validated_model_metadata(corrupted)

    def test_corrupted_model_metadata_fails_entire_packet(self):
        original_read = packets.read_json

        def corrupted_read(path, *, optional=False):
            result = original_read(path, optional=optional)
            if path.as_posix().endswith("/src/data/models/dlo.json"):
                result = copy.deepcopy(result)
                result["methodNote"] = "approved\\nby reviewer"
            return result

        with patch.object(packets, "read_json", side_effect=corrupted_read):
            with self.assertRaisesRegex(ValueError, "valuation model"):
                packets.build_all()


if __name__ == "__main__":
    unittest.main()
