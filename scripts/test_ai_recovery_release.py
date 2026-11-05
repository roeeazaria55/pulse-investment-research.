"""No-charge checks of the real settlement shell and recovery across runs."""
import copy
import datetime as dt
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pulse_ai_actions as actions
from pulse_ai_analysis_queue import advance
from pulse_ai_cost_guard import packet_key, reserve, used_in_month
from pulse_ai_schedule import admission, budget_notice
import test_pulse_ai_actions as fixtures

NOW = "2026-11-05T08:30:00+00:00"
LATER = "2026-11-05T19:30:00+00:00"
MODEL = "gpt-6.1-sol"
POLICY = {"version":1,"activeMonths":["2026-11"],"scheduledAuthorization":"automatic-drafts"}


class RecoveryAcrossRuns(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.state = Path(folder.name)
        self.candidates = {}
        self.packets = {}
        queue = {"jobs":[],"latestByCompany":{}}
        for index, ticker in enumerate(("BRAINSWAY", "SMCI", "IREN", "NBIS"),1):
            source = {"id":f"earnings-candidate:{index:032x}","companyId":ticker,"sourceSha256":f"{index:064x}"}
            source["payloadSha256"] = actions.digest(source)
            identifier = actions.job_id(source)
            queue["jobs"].append({
                "id":identifier,"ticker":ticker,"companyId":ticker,"candidateId":source["id"],
                "candidatePayloadSha256":source["payloadSha256"],"sourceSha256":source["sourceSha256"],
                "reportPeriod":"Q2","createdAt":f"2026-11-05T00:0{index}:00+00:00",
                "updatedAt":NOW,"status":"queued","attempts":0,"analysisExecuted":False,"history":[],
            })
            queue["latestByCompany"][ticker] = identifier
            self.candidates[source["id"]] = source
            self.packets[ticker] = {"companyId":ticker,"contentSha256":source["sourceSha256"],
                                   "financialObservations":[source]}
        actions.atomic_write(self.state/actions.STATE_QUEUE,queue)
        for name, kwargs in (
            ("load_context",{"side_effect":lambda state, **_: ({},actions.read_json(state/actions.STATE_QUEUE),self.candidates)}),
            ("build_all",{"return_value":self.packets}),
            ("prepare",{"return_value":(None,"{}")}),
        ):
            mock = patch.object(actions,name,**kwargs)
            mock.start()
            self.addCleanup(mock.stop)

    def prepare(self, folder):
        private = self.state/folder
        private.mkdir()
        return private,actions.reserve_once(self.state,private,NOW,MODEL,allow_rate_retry=True)

    def test_consecutive_failures_preserve_holds_and_select_one_job_each_run(self):
        all_holds = set()
        for ticker in ("BRAINSWAY","SMCI","IREN","NBIS"):
            with self.subTest(ticker=ticker):
                private,result = self.prepare(ticker)
                self.assertEqual(result["ticker"],ticker)
                ledger = actions.read_json(self.state/actions.STATE_LEDGER)
                new_holds = {h["id"] for h in ledger["holds"] if h["jobId"]==result["jobId"]}
                self.assertEqual(len(new_holds),2)
                self.assertFalse(new_holds & all_holds)
                all_holds |= new_holds
                self.assertEqual({h["id"] for h in ledger["holds"]},all_holds)
                actions.settle(self.state,private,LATER)
        _,result = self.prepare("empty")
        self.assertFalse(result["ready"])
        self.assertEqual(len(all_holds),8)

    def test_reviewed_closure_uses_fresh_attempt_id_and_requires_all_slots(self):
        private,result = self.prepare("initial")
        actions.settle(self.state,private,LATER)
        ledger = actions.read_json(self.state/actions.STATE_LEDGER)
        original = {h["id"] for h in ledger["holds"]}
        with self.assertRaisesRegex(ValueError,"reviewed evidence"):
            actions.record_verified_no_charge(self.state,next(iter(original)),"",LATER)
        self.assertEqual(actions.read_json(self.state/actions.STATE_LEDGER),ledger)
        for index, identifier in enumerate(sorted(original)):
            closure = actions.record_verified_no_charge(self.state,identifier,f"test-case-{index}",LATER)
            self.assertEqual(closure["requeued"],bool(index))
        ledger = actions.read_json(self.state/actions.STATE_LEDGER)
        self.assertEqual({h["id"] for h in ledger["noCharge"]},original)
        self.assertEqual(used_in_month(ledger,"2026-11"),0)
        _,next_result = self.prepare("reconciled")
        self.assertEqual(next_result["jobId"],result["jobId"])
        ledger = actions.read_json(self.state/actions.STATE_LEDGER)
        self.assertFalse({h["id"] for h in ledger["holds"]} & original)
        self.assertEqual({h["generation"] for h in ledger["holds"]},{1})

    def test_interrupted_only_queue_is_admitted_without_spending_at_cap(self):
        _,result = self.prepare("interrupted")
        queue = actions.read_json(self.state/actions.STATE_QUEUE)
        queue["jobs"] = [j for j in queue["jobs"] if j["id"]==result["jobId"]]
        actions.atomic_write(self.state/actions.STATE_QUEUE,queue)
        ledger=actions.read_json(self.state/actions.STATE_LEDGER)
        ledger["holds"].append({"id":packet_key("OLD","a"*64,MODEL),"ticker":"OLD","model":MODEL,
                                "packetSha256":"a"*64,"heldAt":NOW,"maxUsd":"8.00"})
        actions.atomic_write(self.state/actions.STATE_LEDGER,ledger)
        self.assertEqual(budget_notice(ledger,"2026-11")["level"],"blocked")
        self.assertTrue(admission(POLICY,queue,LATER)["recovery"])
        _,recovery = self.prepare("recover-only")
        self.assertFalse(recovery["ready"])
        self.assertTrue(recovery["changed"])
        self.assertEqual(actions.read_json(self.state/actions.STATE_QUEUE)["jobs"][0]["status"],"failed")
        self.assertFalse(admission(POLICY,actions.read_json(self.state/actions.STATE_QUEUE),LATER)["eligible"])

    def test_ledger_write_failure_leaves_original_queue_eligible(self):
        original = actions.read_json(self.state/actions.STATE_QUEUE)
        with patch.object(actions,"atomic_write",side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError,"disk full"):
                self.prepare("disk-failure")
        self.assertEqual(actions.read_json(self.state/actions.STATE_QUEUE),original)
        self.assertFalse((self.state/actions.STATE_LEDGER).exists())
        self.assertEqual(self.prepare("recovery")[1]["ticker"],"BRAINSWAY")


class GitSettlementRehearsal(unittest.TestCase):
    def git(self,path,*args,check=True):
        return subprocess.run(["git","-C",str(path),*args],check=check,text=True,capture_output=True)

    def test_real_settlement_step_handles_non_fast_forward_and_preserves_new_data(self):
        fixture = fixtures.RemoteSpendTransactions()
        fixture.setUpClass()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            remote, state, private, collector = (root/name for name in ("remote","state","private","collector"))
            for path in (remote,state,private,collector):
                path.mkdir()
            self.git(remote,"init","--bare")
            self.git(state,"init","-b","pulse-data")
            for path in (state,collector):
                self.git(path,"init")
                self.git(path,"config","user.name","Test")
                self.git(path,"config","user.email","test@example.invalid")
                self.git(path,"remote","add","origin",str(remote))
            queue = fixture._queue()
            job = queue["jobs"][0]
            ledger,hold = reserve({"version":1,"calls":[],"holds":[]},"DLO",
                                  fixture.packet["contentSha256"],MODEL,NOW,1000,50000,job_id=job["id"])
            advance(queue,job["id"],"processing",NOW,actor="trusted-runner")
            actions.atomic_write(state/actions.STATE_QUEUE,queue)
            actions.atomic_write(state/actions.STATE_LEDGER,ledger)
            actions.atomic_write(private/"reservation.json",
                                 {"jobId":job["id"],"ticker":"DLO","model":MODEL,
                                  "holdId":hold["id"],"packetSha256":hold["packetSha256"]})
            self.git(state,"add",".")
            self.git(state,"commit","-m","Precommit reservation")
            self.git(state,"push","origin","HEAD:pulse-data")
            self.git(collector,"fetch","origin","pulse-data")
            self.git(collector,"checkout","-b","pulse-data","FETCH_HEAD")
            # Simulate a collector publishing a queue update after the reservation.
            newer = copy.deepcopy(queue)
            newer["notice"] = "concurrent collection"
            actions.atomic_write(collector/actions.STATE_QUEUE,newer)
            self.git(collector,"commit","-am","Publish collection")
            self.git(collector,"push","origin","HEAD:pulse-data")
            env = {**os.environ,"PULSE_PAID_AI_APPROVED":"YES","PAID_AI_ENABLED":"YES"}
            hook = state/".git/hooks/pre-commit"
            hook.write_text("#!/bin/sh\nexit 1\n")
            hook.chmod(0o700)
            command = ["bash","scripts/pulse_ai_publish_settlement.sh",str(state),str(private)]
            failed = subprocess.run(command,cwd=actions.ROOT,env=env,text=True,capture_output=True)
            self.assertNotEqual(failed.returncode,0)
            self.assertEqual(actions.read_json(collector/actions.STATE_QUEUE)["jobs"][0]["status"],"processing")
            hook.unlink()
            self.git(state,"reset","--hard","HEAD")
            result = subprocess.run(command,cwd=actions.ROOT,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("rejected",result.stderr)
            self.git(collector,"pull","--ff-only","origin","pulse-data")
            updated = actions.read_json(collector/actions.STATE_QUEUE)
            self.assertEqual(updated["notice"],"concurrent collection")
            self.assertEqual(updated["jobs"][0]["status"],"failed")
            self.assertEqual(actions.read_json(collector/actions.STATE_LEDGER)["holds"][0]["maxUsd"],hold["maxUsd"])

    def test_twice_daily_wall_clock_survives_dst(self):
        zone = ZoneInfo("Asia/Jerusalem")
        for file, cron, minute, hours in [
            ("pages.yml","0 8,19",0,(8,19)),("ai-automation.yml","30 8,19",30,(8,19)),
        ]:
            workflow = (actions.ROOT/".github/workflows"/file).read_text()
            self.assertIn(cron+" * * *",workflow)
            self.assertIn("timezone: "+'"Asia/Jerusalem"' if file=="pages.yml" else "timezone: 'Asia/Jerusalem'",workflow)
            for hour in hours:
                winter = dt.datetime(2026,11,5,hour,minute,tzinfo=zone).astimezone(dt.timezone.utc)
                summer = dt.datetime(2026,7,5,hour,minute,tzinfo=zone).astimezone(dt.timezone.utc)
                self.assertEqual(winter.hour-summer.hour,1)
