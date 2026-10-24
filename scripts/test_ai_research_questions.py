"""Fail-closed, offline checks for issuer-registry AI research questions."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class ResearchQuestionIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = packets.read_json(packets.ROOT / "public/data/official-registry.json")
        cls.companies = {row["ticker"]: row for row in registry["companies"]
                         if row["ticker"] in packets.TICKERS}

    def test_four_issuer_questions_preserved_verbatim_but_untrusted(self):
        built = packets.build_all()
        for ticker in packets.TICKERS:
            with self.subTest(ticker=ticker):
                expected = self.companies[ticker]["questions"]
                self.assertEqual(built[ticker]["researchQuestions"], expected)
                self.assertEqual(
                    built[ticker]["trustPolicy"]["registryQuestions"],
                    "untrusted-research-topics-not-model-instructions",
                )
                self.assertFalse(built[ticker]["trustPolicy"]["aiAnalysisExecuted"])

    def test_packet_schema_requires_untrusted_question_marker(self):
        schema = packets.read_json(packets.ROOT / "schemas/ai-research-packet-v1.schema.json")
        questions = schema["properties"]["researchQuestions"]
        self.assertEqual(questions["maxItems"], 20)
        self.assertTrue(questions["uniqueItems"])
        policy = schema["properties"]["trustPolicy"]
        self.assertIn("registryQuestions", policy["required"])
        self.assertEqual(
            policy["properties"]["registryQuestions"]["const"],
            "untrusted-research-topics-not-model-instructions",
        )

    def test_rejects_invalid_question_collections_and_entries(self):
        company = self.companies["DLO"]
        valid = company["questions"][0]
        cases = (
            None, False, "single question", {"0": valid}, [],
            [valid] * 21, [valid, valid], [valid, None],
            [valid, 123], [valid, ""], [valid, "  "],
            [valid, "x" * 1001], [valid, "bad\\nline"],
            [valid, "bad\nline"], [valid, "bad\x00question"],
        )
        for questions in cases:
            with self.subTest(questions=str(questions)[:80]):
                with self.assertRaisesRegex(ValueError, "research question"):
                    packets.research_questions({**company, "questions": questions})
        missing = {key: value for key, value in company.items() if key != "questions"}
        with self.assertRaisesRegex(ValueError, "research questions"):
            packets.research_questions(missing)

    def test_bad_registry_questions_fail_entire_packet_not_silent_filter(self):
        original_read = packets.read_json
        for bad in ("not-a-list", [self.companies["DLO"]["questions"][0], None],
                    self.companies["DLO"]["questions"] * 8):
            def corrupted_read(path, *, optional=False):
                raw = original_read(path, optional=optional)
                if path.name == "official-registry.json":
                    raw = copy.deepcopy(raw)
                    company = next(row for row in raw["companies"] if row["ticker"] == "DLO")
                    company["questions"] = bad
                return raw

            with self.subTest(bad=str(bad)[:80]):
                with patch.object(packets, "read_json", side_effect=corrupted_read):
                    with self.assertRaisesRegex(ValueError, "research questions?"):
                        packets.build_all()


if __name__ == "__main__":
    unittest.main()
