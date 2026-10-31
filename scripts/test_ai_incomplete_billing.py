"""Regression for a billed response truncated before producing a valid draft."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_optional_ai_review as runner
from pulse_ai_cost_guard import preflight
from pulse_ai_actions import MAX_OUTPUT_TOKENS as RESERVATION_LIMIT

class IncompleteBillingTests(unittest.TestCase):
    def test_incomplete_records_cost_blocks_retry_and_never_writes_draft(self):
        packet = {"contentSha256": "a" * 64}
        response = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                    "usage": {"input_tokens": 7983, "output_tokens": 6000},
                    "output": [{"secret": "PRIVATE RESPONSE"}]}
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "ledger.json"
            target = Path(folder) / "review.json"
            output = io.StringIO()
            with patch.object(runner, "build_strict_format", return_value={}), patch.object(runner, "urlopen") as network, contextlib.redirect_stdout(output):
                network.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
                with self.assertRaisesRegex(ValueError, "max_output_tokens"):
                    runner.run_paid_review("NBIS", packet, "{}", "gpt-6.1-sol", "fake-key", target, ledger)
                payload = json.loads(network.call_args.args[0].data)
                self.assertEqual(payload["max_output_tokens"], RESERVATION_LIMIT)
                self.assertEqual(RESERVATION_LIMIT, 50000)
                self.assertFalse(target.exists())
                billed = runner.read_ledger(ledger)
                self.assertEqual(billed["calls"][0]["usd"], "0.08")
                self.assertEqual(billed["holds"], [])
                with self.assertRaisesRegex(ValueError, "already-processed"):
                    runner.run_paid_review("NBIS", packet, "{}", "gpt-6.1-sol", "fake-key", target, ledger)
                self.assertEqual(network.call_count, 1)
            self.assertIn('"reason": "max_output_tokens"', output.getvalue())
            self.assertNotIn("PRIVATE RESPONSE", output.getvalue())
            self.assertNotIn("fake-key", output.getvalue())

    def test_unknown_diagnostics_are_redacted(self):
        result = runner.response_diagnostics({"status":"SECRET", "incomplete_details":{"reason":"SECRET"}})
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "unknown")

    def test_expanded_output_still_enforces_monthly_budget(self):
        empty = {"version":1,"calls":[],"holds":[]}
        decision = preflight(empty,"NBIS","a"*64,"gpt-6.1-sol","2026-10-31T00:00:00Z",100000,RESERVATION_LIMIT)
        self.assertEqual(decision["estimatedMaxUsd"], "0.70")
        self.assertTrue(decision["allowed"])
        from pulse_ai_cost_guard import reserve
        ledger = empty
        for i in range(12):
            ledger, _ = reserve(ledger,"NBIS",f'{i:064x}',"gpt-6.1-sol","2026-10-31T00:00:00Z",100000,RESERVATION_LIMIT)
        self.assertFalse(preflight(ledger,"NBIS","f"*64,"gpt-6.1-sol","2026-10-31T00:00:00Z",100000,RESERVATION_LIMIT)["allowed"])

if __name__ == '__main__': unittest.main()
