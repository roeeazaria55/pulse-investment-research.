"""Offline queue regression: no OpenAI secret, network, approval or invoice."""
import copy
import json
import unittest
from pulse_ai_analysis_queue import build_queue,validate,advance,job_id,utc_at,ROOT
from earnings_research_candidates import digest

REGISTRY=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))
META=next(c for c in REGISTRY["companies"] if c["ticker"]=="META")
NOW="2026-10-29T11:30:00+00:00"

def candidate(status="needs-review",sha="b"*64,metrics=True):
    c={"id":"earnings-candidate:"+"a"*32,"companyId":META["id"],"ticker":"META",
       "sourceUrl":"https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx",
       "sourceSha256":sha,"reportPeriod":"Q3 2026","firstCandidateAt":"2026-10-21T17:00:00+00:00",
       "publicationStatus":"not-approved","aiAnalysisExecuted":False,
       "status":status,"metrics":[{"id":"revenue"}] if metrics else []}
    c["payloadSha256"]=digest(c)
    return c

def source_store(c):
    return {"version":1,"latestByCompany":{c["companyId"]:c["id"]},"candidates":[c]}

class SourceQueueTests(unittest.TestCase):
    def test_build_source_bound_queue_idempotently(self):
        a=candidate();q=build_queue(source_store(a),{},REGISTRY,NOW)
        self.assertEqual(len(q["jobs"]),1)
        job=q["jobs"][0]
        self.assertEqual(job["status"],"queued")
        self.assertEqual([x["status"] for x in job["history"]],["detected","validated","queued"])
        self.assertFalse(job["analysisExecuted"])
        self.assertEqual(job["publicationStatus"],"not-approved")
        self.assertEqual(job["id"],job_id(a))
        self.assertEqual(build_queue(source_store(a),q,REGISTRY,NOW),q)
        self.assertIs(validate(q,REGISTRY),q)
    def test_unsupported_report_is_not_an_ai_job(self):
        c=candidate(status="blocked")
        q=build_queue(source_store(c),{},REGISTRY,NOW)
        self.assertEqual(q["jobs"][0]["status"],"blocked")
        self.assertEqual(q["jobs"][0]["statusReason"],"source-requires-human-reconciliation")
        c=candidate(metrics=False)
        q=build_queue(source_store(c),{},REGISTRY,NOW)
        self.assertEqual(q["jobs"][0]["status"],"blocked")
    def test_changed_source_creates_new_job_with_history(self):
        a=candidate();q=build_queue(source_store(a),{},REGISTRY,NOW)
        b=candidate(sha="c"*64);b["id"]="earnings-candidate:"+"f"*32;b["payloadSha256"]=digest({k:v for k,v in b.items() if k!="payloadSha256"})
        nextq=build_queue(source_store(b),q,REGISTRY,"2026-10-30T00:00:00Z")
        self.assertEqual(len(nextq["jobs"]),2)
        self.assertNotEqual(nextq["latestByCompany"][a["companyId"]],q["latestByCompany"][a["companyId"]])
    def test_source_tampering_and_domain_spoof_fail_closed(self):
        c=candidate()
        c["sourceUrl"]="https://investor.atmeta.com.evil.example/filing"
        c["payloadSha256"]=digest({k:v for k,v in c.items() if k!="payloadSha256"})
        with self.assertRaisesRegex(ValueError,"Disallowed"):
            build_queue(source_store(c),{},REGISTRY,NOW)
        c=candidate();c["metrics"].append({"id":"fabricated"})
        with self.assertRaisesRegex(ValueError,"corrupted"):
            build_queue(source_store(c),{},REGISTRY,NOW)
    def test_untrusted_approval_and_fake_ai_are_rejected(self):
        c=candidate()
        c["publicationStatus"]="approved"
        c["payloadSha256"]=digest({k:v for k,v in c.items() if k!="payloadSha256"})
        with self.assertRaises(ValueError):
            build_queue(source_store(c),{},REGISTRY,NOW)
        c=candidate();c["aiAnalysisExecuted"]=True
        c["payloadSha256"]=digest({k:v for k,v in c.items() if k!="payloadSha256"})
        with self.assertRaises(ValueError):
            build_queue(source_store(c),{},REGISTRY,NOW)
    def test_illegal_transition_rejected(self):
        c=candidate();q=build_queue(source_store(c),{},REGISTRY,NOW)
        with self.assertRaisesRegex(ValueError,"cannot start AI"):
            advance(q,q["jobs"][0]["id"],"processing",NOW)
        with self.assertRaisesRegex(ValueError,"Illegal"):
            advance(q,q["jobs"][0]["id"],"approved",NOW,actor="owner")
        q["jobs"][0]["status"]="published"
        with self.assertRaisesRegex(ValueError,"disagree"):
            validate(q,REGISTRY)
    def test_valid_workflow_transitions_require_non_collector_actor(self):
        c=candidate();q=build_queue(source_store(c),{},REGISTRY,NOW)
        jid=q["jobs"][0]["id"]
        advance(q,jid,"processing",NOW,actor="trusted-runner")
        advance(q,jid,"draft-ready",NOW,actor="trusted-runner")
        advance(q,jid,"pending-review",NOW,actor="trusted-runner")
        self.assertEqual(validate(q,REGISTRY)["jobs"][0]["status"],"pending-review")
        with self.assertRaises(ValueError):
            advance(q,jid,"published",NOW,actor="trusted-runner")
    def test_bad_history_or_timestamps_are_not_accepted(self):
        q=build_queue(source_store(candidate()),{},REGISTRY,NOW)
        q["jobs"][0]["history"][1]["status"]="approved"
        with self.assertRaises(ValueError):
            validate(q,REGISTRY)
        with self.assertRaises(ValueError):
            utc_at("2026-10-29T11:00:00")

if __name__=="__main__":unittest.main()
