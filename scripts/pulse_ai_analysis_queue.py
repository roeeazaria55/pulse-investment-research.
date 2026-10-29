"""Durable, idempotent public analysis *queue metadata*, never paid AI execution.

A queue entry means an official earnings source warrants a review. It does NOT
mean a model was called or the result has been approved. Existing mutable work
state is restricted by an explicit state machine and source-bound identity.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from earnings_research_candidates import digest, source_allowed, valid_day

ROOT=Path(__file__).resolve().parent.parent
QUEUE=ROOT/"public/data/ai-analysis-queue.json"
CANDIDATES=ROOT/"public/data/earnings-research-candidates.json"
REGISTRY=ROOT/"public/data/official-registry.json"
VALID={"detected","validated","queued","processing","draft-ready","pending-review","approved","published",
       "blocked","failed","pending-budget","rejected","superseded"}
# The public collector may only create pending or blocked entries, never
# promote entries to a paid/model/approved state.
COLLECTOR_MUTABLE={"detected","validated","queued","blocked"}
TERMINAL={"published","rejected","superseded"}
TRANSITIONS={
 "detected":{"validated","blocked"},
 "validated":{"queued","blocked"},
 "queued":{"processing","blocked","pending-budget","superseded"},
 "processing":{"draft-ready","failed","pending-budget"},
 "draft-ready":{"pending-review","blocked"},
 "pending-review":{"approved","rejected","blocked"},
 "approved":{"published","blocked"},
 "failed":{"queued","blocked"},
 "pending-budget":{"queued","blocked"},
 "blocked":{"queued","superseded"},
 "published":set(),"rejected":set(),"superseded":set(),
}

def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)

def utc_at(s):
    if not isinstance(s,str):raise ValueError("Timestamp must be text")
    timestamp=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if timestamp.tzinfo is None:raise ValueError("Timezone required")
    return timestamp.astimezone(dt.timezone.utc).isoformat()

def job_id(candidate):
    if not isinstance(candidate,dict):raise ValueError("Candidate required")
    identity={k:candidate[k] for k in ("id","companyId","sourceSha256","payloadSha256")}
    return "ai-job:"+digest(identity)[:32]

def validate(store,registry):
    if not isinstance(store,dict) or store.get("version")!=1 or not isinstance(store.get("jobs"),list):
        raise ValueError("Malformed queue")
    companies={c["id"]:c for c in registry["companies"]}
    seen=set()
    for job in store["jobs"]:
        if not isinstance(job,dict) or job.get("id") in seen or job.get("status") not in VALID:
            raise ValueError("Duplicate or malformed queue job")
        seen.add(job["id"])
        company=companies.get(job.get("companyId"))
        if company is None or job.get("ticker") != (company.get("ticker") or company["id"]):
            raise ValueError("Queue company identity mismatch")
        if not source_allowed(job.get("sourceUrl"),company):
            raise ValueError("Untrusted source in queue")
        if not isinstance(job.get("sourceSha256"),str) or not re.fullmatch(r"[a-f0-9]{64}",job["sourceSha256"]):
            raise ValueError("Invalid source version")
        if not re.fullmatch(r"earnings-candidate:[a-f0-9]{32}",str(job.get("candidateId"))):
            raise ValueError("Invalid candidate ID")
        if not re.fullmatch(r"[a-f0-9]{64}",str(job.get("candidatePayloadSha256"))):
            raise ValueError("Invalid candidate digest")
        shadow={"id":job["candidateId"],"companyId":job["companyId"],
                "sourceSha256":job["sourceSha256"],"payloadSha256":job["candidatePayloadSha256"]}
        if job.get("id")!=job_id(shadow):
            raise ValueError("Forged job identity")
        if job.get("publicationStatus")!="not-approved" or job.get("approvedModelChange") is not False:
            raise ValueError("Queue cannot publish approved research")
        if not isinstance(job.get("history"),list) or not job["history"]:
            raise ValueError("Missing queue state history")
        prev=None
        for entry in job["history"]:
            if not isinstance(entry,dict) or set(entry)!={"status","at"} or entry["status"] not in VALID:
                raise ValueError("Malformed queue transition")
            utc_at(entry["at"])
            if prev is not None and entry["status"] not in TRANSITIONS[prev]:
                raise ValueError("Illegal queue transition")
            prev=entry["status"]
        if prev!=job["status"] or job["createdAt"]!=job["history"][0]["at"] or job["updatedAt"]!=job["history"][-1]["at"]:
            raise ValueError("Queue state and timestamps disagree")
        if type(job.get("attempts")) is not int or not 0<=job["attempts"]<=5:
            raise ValueError("Invalid attempts")
        if type(job.get("analysisExecuted")) is not bool:
            raise ValueError("Invalid AI execution status")
        if job["analysisExecuted"] and job["status"] in {"detected","validated","queued","blocked"}:
            raise ValueError("Cannot claim AI run in collection queue")
    return store

def advance(store,identifier,status,now,*,actor="collector"):
    if status not in VALID:raise ValueError("Unknown job status")
    now=utc_at(now)
    jobs=store["jobs"]
    found=next((j for j in jobs if j["id"]==identifier),None)
    if found is None:raise ValueError("Job not found")
    if actor=="collector" and status not in COLLECTOR_MUTABLE:
        raise ValueError("Collector cannot start AI, approve or publish")
    if status not in TRANSITIONS[found["status"]]:
        raise ValueError("Illegal queue state transition")
    found["status"]=status
    found["updatedAt"]=now
    found["history"].append({"status":status,"at":now})
    return store

def build_queue(candidates, previous, registry, now):
    now=utc_at(now)
    if not isinstance(candidates,dict) or candidates.get("version")!=1 or not isinstance(candidates.get("candidates"),list):
        raise ValueError("Malformed research candidates")
    companies={c["id"]:c for c in registry["companies"]}
    old=previous if previous else {"version":1,"jobs":[]}
    validate(old,registry)
    saved={j["id"]:j for j in old["jobs"]}
    latest=candidates.get("latestByCompany",{})
    if not isinstance(latest,dict):raise ValueError("Invalid latest pointers")
    known={c["id"]:c for c in candidates["candidates"]}
    for company_id, candidate_id in latest.items():
        if company_id not in companies or candidate_id not in known:
            raise ValueError("Unknown current source candidate")
        c=known[candidate_id]
        company=companies[company_id]
        if c["companyId"]!=company_id or c.get("publicationStatus")!="not-approved" or c.get("aiAnalysisExecuted") is not False:
            raise ValueError("Candidate falsely claims AI execution or approval")
        if not source_allowed(c.get("sourceUrl"),company):
            raise ValueError("Disallowed candidate URL")
        payload=c.get("payloadSha256")
        if not re.fullmatch(r"[a-f0-9]{64}",str(payload)) or digest({k:v for k,v in c.items() if k!="payloadSha256"})!=payload:
            raise ValueError("Source candidate payload corrupted")
        if c.get("status") not in ("needs-review","blocked"):
            raise ValueError("Unknown candidate status")
        if not c.get("reportPeriod") or not isinstance(c.get("metrics"),list):
            status="blocked";reason="missing-report-period-or-metrics"
        elif c["status"]=="blocked" or not c["metrics"]:
            status="blocked";reason="source-requires-human-reconciliation"
        else:
            status="queued";reason="verified-source-candidate-awaits-ai"
        identifier=job_id(c)
        if identifier in saved:
            continue
        first=utc_at(c["firstCandidateAt"])
        history=[{"status":"detected","at":first},{"status":"validated","at":now}]
        if status=="queued":history.append({"status":"queued","at":now})
        else:history.append({"status":"blocked","at":now})
        saved[identifier]={
            "id":identifier,"candidateId":c["id"],"companyId":company_id,
            "ticker":c.get("ticker") or company.get("ticker") or company_id,
            "sourceUrl":c["sourceUrl"],"sourceSha256":c["sourceSha256"],
            "candidatePayloadSha256":payload,"reportPeriod":c.get("reportPeriod"),
            "createdAt":first,"updatedAt":now,"status":status,
            "statusReason":reason,"attempts":0,"analysisExecuted":False,
            "publicationStatus":"not-approved","approvedModelChange":False,
            "history":history,
        }
    current={cid:job_id(known[cid_]) for cid,cid_ in latest.items()}
    return {"version":1,
            "updatedAt":now if len(saved)>len(old["jobs"]) else old.get("updatedAt",now),
            "jobs":sorted(saved.values(),key=lambda j:(j["companyId"],j["createdAt"],j["id"])),
            "latestByCompany":current,
            "notice":"Queue state only; no API request, model execution or approved research."}

def main():
    old=json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else {}
    registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
    candidates=json.loads(CANDIDATES.read_text(encoding="utf-8"))
    new=build_queue(candidates,old,registry,dt.datetime.now(dt.timezone.utc).isoformat())
    validate(new,registry)
    if new!=old:
        QUEUE.parent.mkdir(parents=True,exist_ok=True)
        tmp=QUEUE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        tmp.replace(QUEUE)
    print(json.dumps({"jobs":len(new["jobs"]),"queued":sum(j["status"]=="queued" for j in new["jobs"]),
                      "blocked":sum(j["status"]=="blocked" for j in new["jobs"]),
                      "paidAiExecuted":False,"approvedResearchChanged":False}))

if __name__=="__main__":main()
