"""Offline, fail-closed checks for existing analyst valuation assumptions.

These tests do not calculate or modify targets, models or probabilities.
"""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_research_packets as packets


class ModelInputShapeIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = packets.read_json(packets.ROOT / "public/data/official-registry.json")
        cls.companies = {row["ticker"]: row for row in registry["companies"]
                         if row["ticker"] in packets.TICKERS}

    def test_existing_models_preserved_verbatim_as_unverified_assumptions(self):
        built = packets.build_all()
        for ticker in ("DLO", "NBIS", "IREN"):
            with self.subTest(ticker=ticker):
                original = packets.read_json(
                    packets.ROOT / "src/data/models" / (ticker.lower() + ".json"))
                assumptions = built[ticker]["valuationModel"]["assumptions"]
                self.assertEqual(
                    assumptions,
                    [{key: scenario.get(key) for key in
                      ("id", "label", "probability", "inputs", "rationale")}
                     for scenario in original["scenarios"]],
                )
                self.assertIsNone(built[ticker]["valuationModel"]["approvedTargetPrice"])
                self.assertTrue(built[ticker]["valuationModel"]["noAutomaticUpdate"])
        self.assertIsNone(built["SMCI"]["valuationModel"])

    def test_rejects_missing_duplicated_or_invalid_scenario_fields(self):
        company = self.companies["DLO"]
        original = packets.read_json(packets.ROOT / "src/data/models/dlo.json")
        cases = []

        def changed(mutator):
            model = copy.deepcopy(original)
            mutator(model)
            cases.append(model)

        changed(lambda m: m.pop("scenarios"))
        changed(lambda m: m.__setitem__("scenarios", "bear/base/bull"))
        changed(lambda m: m.__setitem__("scenarios", []))
        changed(lambda m: m.__setitem__("scenarios", m["scenarios"][:2]))
        changed(lambda m: m["scenarios"][1].__setitem__("id", "bear"))
        changed(lambda m: m["scenarios"][1].__setitem__("id", "upside"))
        changed(lambda m: m["scenarios"][0].pop("inputs"))
        changed(lambda m: m["scenarios"][0].__setitem__("inputs", "not-an-object"))
        changed(lambda m: m["scenarios"][0].__setitem__("inputs", {}))
        changed(lambda m: m["scenarios"][0]["inputs"].__setitem__("driver", "999"))
        changed(lambda m: m["scenarios"][0]["inputs"].__setitem__("driver", float("nan")))
        changed(lambda m: m["scenarios"][0].pop("rationale"))
        changed(lambda m: m["scenarios"][0].__setitem__("probability", True))
        changed(lambda m: m["scenarios"][0].__setitem__("probability", 101))
        changed(lambda m: m["scenarios"][0].__setitem__("probability", 21))
        changed(lambda m: m.__setitem__("ticker", "NBIS"))
        changed(lambda m: m.__setitem__("companyId", "candidate-nebius"))
        changed(lambda m: m.__setitem__("version", 2))
        cases.extend([None, [], "not-a-model"])

        for case in cases:
            with self.subTest(case=str(case)[:120]):
                with self.assertRaisesRegex(ValueError, "valuation"):
                    packets.validated_model_scenarios(case, company)

    def test_invalid_model_fails_packet_generation_instead_of_silent_omission(self):
        original_read = packets.read_json
        for corruption in ("scenarios", "probability", "inputs"):
            def corrupted_read(path, *, optional=False):
                raw = original_read(path, optional=optional)
                if path.as_posix().endswith("/src/data/models/dlo.json"):
                    raw = copy.deepcopy(raw)
                    if corruption == "scenarios":
                        raw.pop("scenarios")
                    elif corruption == "probability":
                        raw["scenarios"][0]["probability"] = "20"
                    else:
                        raw["scenarios"][0]["inputs"] = []
                return raw

            with self.subTest(corruption=corruption):
                with patch.object(packets, "read_json", side_effect=corrupted_read):
                    with self.assertRaisesRegex(ValueError, "valuation"):
                        packets.build_all()


if __name__ == "__main__":
    unittest.main()
