"""Offline integrity tests for unverified historical model quote references.

No market lookup, paid AI, valuation changes or model recalculation.
"""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class ModelReferenceIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = packets.read_json(packets.ROOT / "public/data/official-registry.json")
        cls.companies = {row["ticker"]: row for row in registry["companies"]
                         if row["ticker"] in packets.TICKERS}

    def test_existing_historical_references_are_preserved_without_approval(self):
        built = packets.build_all()
        for ticker in ("DLO", "NBIS", "IREN"):
            with self.subTest(ticker=ticker):
                original = packets.read_json(
                    packets.ROOT / "src/data/models" / (ticker.lower() + ".json"))
                self.assertEqual(built[ticker]["valuationModel"]["referencePrice"],
                                 original["reference"])
                self.assertIsNone(built[ticker]["valuationModel"]["approvedTargetPrice"])
                self.assertTrue(built[ticker]["valuationModel"]["noAutomaticUpdate"])
        self.assertIsNone(built["SMCI"]["valuationModel"])

    def test_rejects_malformed_historical_quote_and_model_dates(self):
        company = self.companies["DLO"]
        original = packets.read_json(packets.ROOT / "src/data/models/dlo.json")
        cases = []

        def changed(label, mutate):
            model = copy.deepcopy(original)
            mutate(model)
            cases.append((label, model))

        changed("missing reference", lambda m: m.pop("reference"))
        changed("reference string", lambda m: m.__setitem__("reference", "14.67"))
        changed("missing price", lambda m: m["reference"].pop("price"))
        changed("extra authority", lambda m: m["reference"].__setitem__("approved", True))
        for value in (None, "14.67", True, 0, -1, float("nan"), float("inf")):
            changed("invalid price " + repr(value),
                    lambda m, value=value: m["reference"].__setitem__("price", value))
        for value in ("not-a-date", "2026-13-01", "2026-10-20", None):
            changed("invalid quote date " + repr(value),
                    lambda m, value=value: m["reference"].__setitem__("date", value))
        for value in ("https://evil.example/stocks/dlo/history/",
                      "https://stockanalysis.com.evil.example/stocks/dlo/history/",
                      "https://stockanalysis.com@evil.example/stocks/dlo/history/",
                      "https://user@stockanalysis.com/stocks/dlo/history/",
                      "http://stockanalysis.com/stocks/dlo/history/",
                      "https://stockanalysis.com:8443/stocks/dlo/history/",
                      "https://stockanalysis.com/stocks/nbis/history/",
                      "https://stockanalysis.com/stocks/dlo/history/?verified=1",
                      "https://stockanalysis.com/stocks/dlo/history/#approved",
                      "https://stockanalysis.com/stocks/dlo/history/\\nspoof",
                      "https://stockanalysis.com/stocks/dlo/history/\nspoof",
                      "javascript:alert(1)", 42):
            changed("invalid URL " + repr(value),
                    lambda m, value=value: m["reference"].__setitem__("url", value))
        for value in ("", "   ", "Approved\nquote", "Approved\\nquote", 17):
            changed("invalid label " + repr(value),
                    lambda m, value=value: m["reference"].__setitem__("label", value))
        for key, value in (("analysisDate", "2026-99-01"),
                           ("analysisDate", None),
                           ("horizonDate", "2026-10-19"),
                           ("horizonDate", "2026-10-18"),
                           ("horizonDate", "bad-date")):
            changed("invalid model date " + key + " " + repr(value),
                    lambda m, key=key, value=value: m.__setitem__(key, value))

        for label, model in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, "valuation model"):
                    packets.validated_model_reference(model, company)

    def test_invalid_reference_fails_entire_packet_instead_of_becoming_null(self):
        original_read = packets.read_json

        def corrupted_read(path, *, optional=False):
            data = original_read(path, optional=optional)
            if path.as_posix().endswith("/src/data/models/dlo.json"):
                data = copy.deepcopy(data)
                data["reference"]["url"] = "https://evil.example/stocks/dlo/history/"
            return data

        with patch.object(packets, "read_json", side_effect=corrupted_read):
            with self.assertRaisesRegex(ValueError, "valuation model"):
                packets.build_all()


if __name__ == "__main__":
    unittest.main()
