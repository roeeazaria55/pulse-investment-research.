"""Regression tests for scheduled AI recovery without network or paid usage."""
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pulse_ai_actions as actions
import run_optional_ai_review as runner
from pulse_ai_cost_guard import packet_key, reserve, used_in_month

NOW = "2026-11-01T13:41:49.240819+00:00"
LATER = "2026-11-05T09:00:00+00:00"
MODEL = "gpt-6.1-sol"
PACKET = {"contentSha256": "a"*64}
JOB = "ai-job:"+"a"*32


def rejection(code, delay="7"):
    headers = Message()
    headers["Retry-After"] = delay
    return HTTPError(runner.ENDPOINT, 429, "rate limit", headers,
                     io.BytesIO(json.dumps({"error": {"code": code, "message": "PRIVATE"}}).encode()))


class DispatchRecovery(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.state = Path(folder.name)/"state"
        self.private = Path(folder.name)/"private"
        self.state.mkdir()
        self.private.mkdir()
        self.ledger = self.private/"ledger.json"
        self.job = {"id":JOB,"ticker":"SMCI","status":"processing","updatedAt":NOW,
                    "history":[{"status":"processing","at":NOW}]}
        self.queue = {"jobs":[self.job]}
        ledger = {"version":1,"calls":[],"holds":[]}
        ledger, self.first = reserve(ledger, "SMCI", PACKET["contentSha256"], MODEL, NOW,
                                     1000, 50000, job_id=JOB)
        ledger, self.retry = reserve(ledger, "SMCI", PACKET["contentSha256"], MODEL, NOW,
                                     1000, 50000, job_id=JOB, rate_retry=True)
        actions.atomic_write(self.state/actions.STATE_LEDGER,ledger)
        actions.atomic_write(self.ledger,ledger)
        actions.atomic_write(self.private/"reservation.json",
                             {"jobId":JOB,"ticker":"SMCI","model":MODEL,
                              "holdId":self.first["id"],"packetSha256":PACKET["contentSha256"]})

    def run_review(self):
        runner.run_paid_review("SMCI", PACKET, "{}", MODEL, "fake-key", self.private/"review.json",
                               self.ledger, reservation_precommitted=True)

    def settle(self):
        with patch.object(actions,"load_context",return_value=({},self.queue,{})):
            return actions.settle(self.state,self.private,LATER)

    def test_rate_limit_retry_records_usage_and_retains_first_exposure(self):
        with patch.object(runner,"urlopen") as network, patch.object(runner.time,"sleep") as sleep, \
             patch.object(runner,"build_strict_format",return_value={}):
            response = network.return_value
            response.__enter__.return_value.read.return_value = json.dumps(
                {"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"},
                 "usage":{"input_tokens":100,"output_tokens":100}}).encode()
            network.side_effect = [rejection(runner.RATE_LIMIT), response]
            with self.assertRaisesRegex(ValueError,"max_output_tokens"):
                self.run_review()
        sleep.assert_called_once_with(7)
        self.assertEqual([call.args[0].get_header("X-client-request-id") for call in network.call_args_list],
                         [self.first["id"],self.retry["id"]])
        self.assertTrue(self.settle()["settled"])
        ledger = actions.read_json(self.state/actions.STATE_LEDGER)
        self.assertEqual(ledger["calls"][0]["id"],self.retry["id"])
        self.assertEqual(ledger["holds"][0]["reconciliation"],runner.RATE_LIMIT)
        self.assertFalse((self.private/"review.json").exists())

    def test_quota_unknown_and_long_retry_after_do_not_replay(self):
        for provider_code, expected, delay in [(runner.QUOTA,runner.QUOTA,"7"),
            ("other",runner.UNKNOWN_429,"7"),(runner.RATE_LIMIT,runner.RATE_LIMIT,"600")]:
            with self.subTest(code=provider_code):
                with patch.object(runner,"urlopen",side_effect=rejection(provider_code,delay)) as network, \
                     patch.object(runner.time,"sleep") as sleep, \
                     patch.object(runner,"build_strict_format",return_value={}):
                    with self.assertRaisesRegex(ValueError,"billing reconciliation required"):
                        self.run_review()
                network.assert_called_once()
                sleep.assert_not_called()
                self.assertEqual(self.settle()["status"],expected)
                ledger = actions.read_json(self.state/actions.STATE_LEDGER)
                self.assertEqual([hold["id"] for hold in ledger["holds"]],[self.first["id"]])
                self.assertEqual(ledger["calls"],[])
                # Each case starts with its own durable precommit and private files.
                self.setUp()

    def test_repeated_rate_limit_exhausts_reserved_slots(self):
        with patch.object(runner,"urlopen",side_effect=[rejection(runner.RATE_LIMIT),
              rejection(runner.RATE_LIMIT)]) as network, patch.object(runner.time,"sleep"), \
             patch.object(runner,"build_strict_format",return_value={}):
            with self.assertRaisesRegex(ValueError,"request rate limit"):
                self.run_review()
        self.assertEqual(network.call_count,2)
        self.assertEqual(self.settle()["status"],runner.RATE_LIMIT)
        self.assertEqual(len(actions.read_json(self.state/actions.STATE_LEDGER)["holds"]),2)

    def test_parallel_replay_and_transport_failure_keep_one_uncertain_slot(self):
        def attempt():
            try:
                self.run_review()
            except (FileExistsError, URLError) as error:
                return type(error)
            self.fail("Expected network failure or an already claimed attempt")

        with patch.object(runner,"urlopen",side_effect=URLError("offline")) as network, \
             patch.object(runner,"build_strict_format",return_value={}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertCountEqual(pool.map(lambda _: attempt(),range(2)),[URLError,FileExistsError])
        network.assert_called_once()
        self.assertEqual(self.settle()["status"],"billing-reconciliation-required")
        self.assertEqual(len(actions.read_json(self.state/actions.STATE_LEDGER)["holds"]),1)

    def test_missing_private_billing_evidence_never_releases_reservations(self):
        self.ledger.unlink()
        self.assertFalse(self.settle()["settled"])
        ledger = actions.read_json(self.state/actions.STATE_LEDGER)
        self.assertEqual(len(ledger["holds"]),2)
        self.assertEqual(self.job["status"],"failed")


class QueueRecovery(unittest.TestCase):
    def test_interrupted_legacy_brainsway_does_not_block_iren_or_nbis(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            ticker = "candidate-brainsway"
            ledger = {"version":1,"calls":[],"holds":[{"id":packet_key(ticker,"b"*64,MODEL),
                      "ticker":ticker,"model":MODEL,"packetSha256":"b"*64,"heldAt":NOW,"maxUsd":"0.54"}]}
            stalled = {"id":JOB,"ticker":ticker,"status":"processing","updatedAt":NOW,
                       "history":[{"status":"processing","at":NOW}],"reportPeriod":"Q2"}
            queue = {"jobs":[stalled],"latestByCompany":{}}
            self.assertTrue(actions.recover_interrupted(queue,ledger,LATER))
            self.assertEqual(stalled["status"],"failed")
            self.assertEqual(ledger["holds"][0]["jobId"],JOB)
            self.assertEqual(str(used_in_month(ledger,"2026-12")),"0.54")
            actions.atomic_write(state/actions.STATE_LEDGER,ledger)
            for company in ("IREN","NBIS","SMCI"):
                with self.subTest(company=company):
                    self.check_selection(state,queue,ticker,company)

    def check_selection(self,state,queue,brainsway,ticker):
        jobs = []
        packets = {}
        for index, issuer in enumerate((brainsway,ticker),1):
            candidate = {"id":f"earnings-candidate:{index:032x}","companyId":issuer,"sourceSha256":"b"*64}
            candidate["payloadSha256"] = actions.digest(candidate)
            job = {"id":actions.job_id(candidate),"ticker":issuer,"companyId":issuer,"status":"queued",
                   "candidateId":candidate["id"],"candidatePayloadSha256":candidate["payloadSha256"],
                   "sourceSha256":"b"*64,"createdAt":NOW,"reportPeriod":"Q2"}
            jobs.append((job,candidate))
            packets[issuer] = {"companyId":issuer,"contentSha256":"c"*64,
                               "financialObservations":[{"sourceSha256":"b"*64}]}
        current = {"jobs":[*queue["jobs"],*(job for job,_ in jobs)],
                   "latestByCompany":{job["companyId"]:job["id"] for job,_ in jobs}}
        candidates = {c["id"]:c for _,c in jobs}
        with patch.object(actions,"load_context",return_value=({},current,candidates)), \
             patch.object(actions,"build_all",return_value=packets), \
             patch.object(actions,"prepare",return_value=(None,"{}")):
            selected,_,_ = actions.choose(state,MODEL)
        self.assertEqual(selected["ticker"],ticker)
