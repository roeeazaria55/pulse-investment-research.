"""Offline $10/month PULSE AI spend guard regressions; no network or API usage."""
import unittest
from decimal import Decimal
from pulse_ai_cost_guard import (
 BUDGET_USD, MODEL_RATES, cents, quoted_cost, preflight, reserve, record_call,
 used_in_month, validate_ledger, packet_key
)

EMPTY={"version":1,"calls":[],"holds":[]}
SHA="a"*64
NOW="2026-10-29T09:00:00+00:00"

class AIExpenseTests(unittest.TestCase):
    def test_estimated_price_and_model_allowlist(self):
        self.assertEqual(BUDGET_USD,Decimal("10"))
        self.assertIn("gpt-6-luna", MODEL_RATES)
        self.assertIn("gpt-6.1-sol",MODEL_RATES)
        self.assertEqual(cents(quoted_cost("gpt-6.1-sol",30000,6000)),Decimal(".12"))
        self.assertLess(quoted_cost("gpt-6-luna",30000,6000),
                        quoted_cost("gpt-6.1-sol",30000,6000))
        with self.assertRaisesRegex(ValueError,"Model"):
            quoted_cost("gpt-unapproved",100,100)
    def test_reservation_blocks_duplicates_even_before_response(self):
        ledger,hold=reserve(EMPTY,"META",SHA,"gpt-6.1-sol",NOW,60000,2200)
        self.assertEqual(len(ledger["holds"]),1)
        decision=preflight(ledger,"META",SHA,"gpt-6.1-sol",NOW,60000,2200)
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"],"already-processed-or-reserved")
        self.assertGreater(used_in_month(ledger,"2026-10"),Decimal("0"))
        valid,receipt=record_call(ledger,"META",SHA,"gpt-6.1-sol",NOW,
            {"input_tokens":1000,"output_tokens":400,
             "input_tokens_details":{"cached_tokens":300}})
        self.assertFalse(valid["holds"])
        self.assertEqual(valid["calls"][0]["usd"],receipt["usd"])
        self.assertEqual(valid["calls"][0]["id"],hold["id"])
        self.assertFalse(preflight(valid,"META",SHA,"gpt-6.1-sol",NOW,60000)["allowed"])
    def test_reserve_before_bill_and_no_retry_on_incomplete_usage(self):
        ledger,hold=reserve(EMPTY,"DLO",SHA,"gpt-6.1-sol",NOW,5000)
        with self.assertRaises(ValueError):
            record_call(ledger,"DLO",SHA,"gpt-6.1-sol",NOW,{"input_tokens":1})
        self.assertFalse(preflight(ledger,"DLO",SHA,"gpt-6.1-sol",NOW,5000)["allowed"])
        with self.assertRaisesRegex(ValueError,"No prior"):
            record_call(EMPTY,"META",SHA,"gpt-6.1-sol",NOW,{"input_tokens":1,"output_tokens":1})
    def test_guard_blocks_at_nine_dollars_and_per_call_ceiling(self):
        calls=[]
        for i in range(9):
            sha=("%064x"%(i+1))
            call_id=packet_key("META",sha,"gpt-6.1-sol")
            calls.append({"id":call_id,"ticker":"META","model":"gpt-6.1-sol","packetSha256":sha,
                "calledAt":NOW,"inputTokens":0,"outputTokens":100000,"cachedTokens":0,"usd":"1.00"})
        ledger={"version":1,"calls":calls,"holds":[]}
        self.assertFalse(preflight(ledger,"FTAI",SHA,"gpt-6.1-sol",NOW,4000)["allowed"])
        self.assertEqual(preflight(EMPTY,"FTAI",SHA,"gpt-6.1-sol",NOW,800000)["reason"],"per-call-limit")
    def test_invalid_id_or_price_is_never_trusted(self):
        ledger,hold=reserve(EMPTY,"META",SHA,"gpt-6.1-sol",NOW,6000)
        ledger["holds"][0]["maxUsd"]="-1"
        with self.assertRaises(ValueError):
            validate_ledger(ledger)
        with self.assertRaises(ValueError):
            packet_key("META","wrong","gpt-6.1-sol")
    def test_active_month_only_and_utc_month_boundaries(self):
        old,hold=reserve(EMPTY,"META",SHA,"gpt-6.1-sol","2026-10-31T23:59:59Z",6000)
        self.assertGreater(used_in_month(old,"2026-10"),Decimal("0"))
        self.assertEqual(used_in_month(old,"2026-11"),Decimal("0"))
        self.assertTrue(preflight(old,"FTAI","b"*64,"gpt-6.1-sol","2026-11-01T00:00:00Z",6000)["allowed"])

if __name__=="__main__":unittest.main()
