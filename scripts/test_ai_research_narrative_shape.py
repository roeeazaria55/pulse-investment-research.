"""Offline fail-closed checks for unverified analyst research packet narratives."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class AnalystResearchNarrativeShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = packets.read_json(packets.ROOT / "public/data/official-registry.json")
        cls.dlo = next(row for row in registry["companies"] if row["ticker"] == "DLO")

    def test_existing_four_issuer_narratives_remain_unverified_and_complete(self):
        built = packets.build_all()
        for ticker in packets.TICKERS:
            with self.subTest(ticker=ticker):
                research = built[ticker]["research"]
                self.assertIsNotNone(research)
                self.assertTrue(research["sections"])
                self.assertIsInstance(research["limitations"], list)
                self.assertEqual(research["reviewStatus"], "analyst-research-unverified")
                self.assertTrue(all(section["untrustedInstructions"]
                                    for section in research["sections"].values()))

    def test_malformed_sections_and_limitations_fail_closed(self):
        original_read = packets.read_json
        cases = (
            ("fields", None), ("fields", False), ("fields", []),
            ("fields", ""), ("fields", {}), ("fields", {"other": "ignored"}),
            ("fields", {"thesis": None}),
            ("missing", "a caveat, not a list"),
            ("missing", {"note": "cannot be coerced"}),
            ("missing", ["valid", 7]),
            ("missing", ["valid"] * 31),
            ("asOf", "not-a-date"),
            ("asOf", "2026-99-99"),
        )
        for field, value in cases:
            def corrupted_read(path, *, optional=False):
                raw = original_read(path, optional=optional)
                if path.name == "dlo.json":
                    raw = copy.deepcopy(raw)
                    raw["analysis"][field] = value
                return raw

            with self.subTest(field=field, value=value):
                with patch.object(packets, "read_json", side_effect=corrupted_read):
                    with self.assertRaisesRegex(ValueError, "Malformed analyst research"):
                        packets.research_for(self.dlo, [])

    def test_invalid_wrapper_or_scope_fails_closed(self):
        original_read = packets.read_json
        cases = (
            {"analysis": None},
            {"analysis": []},
            {"analysis": "untrusted"},
            {"scope": {"approved": True}},
            {"scope": []},
        )
        for changes in cases:
            def corrupted_read(path, *, optional=False):
                raw = original_read(path, optional=optional)
                if path.name == "dlo.json":
                    raw = copy.deepcopy(raw)
                    raw.update(changes)
                return raw

            with self.subTest(changes=changes):
                with patch.object(packets, "read_json", side_effect=corrupted_read):
                    with self.assertRaisesRegex(ValueError, "Malformed analyst research"):
                        packets.research_for(self.dlo, [])

    def test_limitation_is_not_split_into_characters_or_silently_truncated(self):
        original_read = packets.read_json
        def corrupted_read(path, *, optional=False):
            raw = original_read(path, optional=optional)
            if path.name == "dlo.json":
                raw = copy.deepcopy(raw)
                raw["analysis"]["missing"] = ["first caveat", "second caveat"]
            return raw

        with patch.object(packets, "read_json", side_effect=corrupted_read):
            result = packets.research_for(self.dlo, [])
        self.assertEqual(result["limitations"], ["first caveat", "second caveat"])
        self.assertEqual(result["reviewStatus"], "analyst-research-unverified")


if __name__ == "__main__":
    unittest.main()
