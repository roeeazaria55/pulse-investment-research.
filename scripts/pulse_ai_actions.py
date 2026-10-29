"""GitHub Actions AI transaction preparation and settlement; NEVER calls OpenAI.

The trusted Actions workflow first commits and pushes an immutable reservation
to pulse-data, then invokes the separately gated private API runner. If the
API call or settlement fails, the reservation remains outstanding and that
report cannot be automatically retried. This is a cost guard, not a substitute
for OpenAI project billing limits.

No operation in this file approves or publishes an investment thesis.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path

from ai_research_packets import build_all
from earnings_research_candidates import digest
from pulse_ai_analysis_queue import ROOT,advance,validate,job_id,utc_at
from pulse_ai_cost_guard import MODEL_RATES,preflight,reserve,packet_key,validate_ledger
from pulse_ai_research_drafts import append_public,build_public_draft,canonical
from run_optional_ai_review import MAX_OUTPUT_TOKENS,MAX_INPUT_BYTES,prepare

STATE_QUEUE="public/data/ai-analysis-queue.json"
STATE_LEDGER="public/data/ai-cost-ledger.json"
STATE_REVIEWS="public/data/ai-research-drafts.json"
PACKET_CANDIDATES="public/data/earnings-research-candidates.json"

def read_json(path,optional=False):
    if not path.exists():
        if optional:return None
        raise ValueError("Missing authoritative state: "+path.name)
    return json.loads(path.read_text(encoding="utf-8"))

def atomic_write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    tmp.replace(path)

def private_write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError("Private run metadata already exists")
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2,allow_nan=False)

def load_context(state):
    registry=read_json(ROOT/"public/data/official-registry.json")
    queue=validate(read_json(state/STATE_QUEUE),registry)
    candidates=read_json(ROOT/PACKET_CANDIDATES)
    by_id={c["id"]:c for c in candidates["candidates"]}
    return registry,queue,by_id

def choose(state,model):
    if model not in MODEL_RATES:raise ValueError("Unsupported model")
    _,queue,candidates=load_context(state)
    jobs=sorted((j for j in queue["jobs"] if j["status"]=="queued"
       and queue["latestByCompany"].get(j["companyId"])==j["id"]),
       key=lambda j:(j["createdAt"],j["id"]))
    packets=build_all()
    for j in jobs:
        source=candidates.get(j["candidateId"])
        if (source is None or job_id(source)!=j["id"]
            or source["payloadSha256"]!=j["candidatePayloadSha256"]
            or digest({k:v for k,v in source.items() if k!="payloadSha256"})!=source["payloadSha256"]):
            raise ValueError("Candidate changed before queued AI task")
        packet=packets.get(j["ticker"])
        if packet is None or packet["companyId"]!=j["companyId"]:
            raise ValueError("Issuer packet mismatch")
        supported={ob["sourceSha256"] for ob in packet["financialObservations"]}
        issuer=packet.get("latestIssuerResearch") or {}
        report=issuer.get("report") or {}
        if issuer.get("sourceBoundMetrics"):
            supported.add(report.get("digest"))
        if j["sourceSha256"] not in supported:
            # Do not pay for an unsupported or missing report.
            continue
        _,payload=prepare(j["ticker"])
        if len(payload.encode("utf-8"))>MAX_INPUT_BYTES:
            continue
        return j,packet,payload
    return None,None,None

def reserve_once(state,private,now,model):
    """Prepare worktree files; workflow MUST git push them before a model call."""
    now=utc_at(now)
    _,queue,_=load_context(state)
    selected,packet,payload=choose(state,model)
    if selected is None:return {"ready":False,"changed":False,"reason":"no-source-supported-queued-job"}
    ledger=read_json(state/STATE_LEDGER,optional=True) or {"version":1,"calls":[],"holds":[]}
    ledger=validate_ledger(ledger)
    decision=preflight(ledger,selected["ticker"],packet["contentSha256"],model,now,
       input_token_ceiling=min(100000,len(payload.encode("utf-8"))*2),
       output_token_ceiling=MAX_OUTPUT_TOKENS)
    if not decision["allowed"]:
        if decision["reason"] in ("monthly-reserve","per-call-limit"):
            advance(queue,selected["id"],"pending-budget",now,actor="trusted-runner")
            selected["statusReason"]=decision["reason"]
            atomic_write(state/STATE_QUEUE,queue)
            return {"ready":False,"changed":True,"reason":decision["reason"]}
        return {"ready":False,"changed":False,"reason":decision["reason"]}
    ledger,hold=reserve(ledger,selected["ticker"],packet["contentSha256"],model,now,
       input_ceiling=min(100000,len(payload.encode("utf-8"))*2),
       output_ceiling=MAX_OUTPUT_TOKENS)
    advance(queue,selected["id"],"processing",now,actor="trusted-runner")
    selected["attempts"]+=1
    selected["statusReason"]="precharged-reservation-awaits-api"
    # Both changes will be committed and git-pushed atomically as one commit.
    atomic_write(state/STATE_LEDGER,ledger)
    atomic_write(state/STATE_QUEUE,queue)
    private_write(private/"reservation.json",{
        "jobId":selected["id"],"ticker":selected["ticker"],"model":model,
        "packetSha256":packet["contentSha256"],"heldAt":hold["heldAt"],
        "holdId":hold["id"]})
    return {"ready":True,"changed":True,"ticker":selected["ticker"],"model":model,
            "jobId":selected["id"],"estimatedMaxUsd":hold["maxUsd"]}

def settle(state,private,now):
    """Persist billed usage and publish only an UNAPPROVED draft. Caller must push."""
    now=utc_at(now)
    reservation=read_json(private/"reservation.json")
    model=reservation["model"]
    registry,queue,_=load_context(state)
    job=next((j for j in queue["jobs"] if j["id"]==reservation["jobId"]),None)
    if job is None or job["status"]!="processing" or job["ticker"]!=reservation["ticker"]:
        raise ValueError("Pre-paid queue reservation not current")
    before=validate_ledger(read_json(state/STATE_LEDGER))
    remote_hold=[h for h in before.get("holds",[]) if h["id"]==reservation["holdId"]]
    if len(remote_hold)!=1 or remote_hold[0]["packetSha256"]!=reservation["packetSha256"]:
        raise ValueError("Remote reservation no longer matches")
    private_ledger=validate_ledger(read_json(private/"ledger.json"))
    receipts=[r for r in private_ledger["calls"] if r["id"]==reservation["holdId"]]
    if len(receipts)!=1:
        raise ValueError("No recorded API usage; leave reservation for manual billing reconciliation")
    # No additional spending may be recorded between the private and remote
    # snapshots; the Actions workflow's concurrency and Git CAS protect this.
    exp=[h for h in before.get("holds",[]) if h["id"]!=reservation["holdId"]]
    if private_ledger.get("holds",[])!=exp or len(private_ledger["calls"])!=len(before["calls"])+1:
        raise ValueError("Cost ledger changed during billed analysis")
    if private_ledger["calls"][:-1]!=before["calls"]:
        raise ValueError("Cost ledger tampering")
    packet=build_all()[job["ticker"]]
    if packet["contentSha256"]!=reservation["packetSha256"]:
        raise ValueError("Source packet changed after the paid request")
    proposal_path=private/"review.json"
    try:
        proposal=read_json(proposal_path)
        if proposal.get("version")==2:
            from pulse_ai_full_research import build_public_full_research_draft
            draft=build_public_full_research_draft(packet,proposal,model,execution_attested=True)
        else:
            draft=build_public_draft(packet,proposal,model,execution_attested=True)
    except (ValueError,KeyError,TypeError,OSError):
        # If a paid response was malformed, record ACTUAL billing anyway,
        # mark it failed and never publish the unsafe text.
        advance(queue,job["id"],"failed",now,actor="trusted-runner")
        job["statusReason"]="model-output-rejected-after-billing"
        atomic_write(state/STATE_LEDGER,private_ledger)
        atomic_write(state/STATE_QUEUE,queue)
        return {"settled":True,"draft":False,"status":"failed-invalid-output"}
    archive=read_json(state/STATE_REVIEWS,optional=True) or {}
    updated=append_public(archive,draft,now)
    advance(queue,job["id"],"draft-ready",now,actor="trusted-runner")
    advance(queue,job["id"],"pending-review",now,actor="trusted-runner")
    job["statusReason"]="unverified-ai-draft-awaits-owner-review"
    job["analysisExecuted"]=True
    atomic_write(state/STATE_LEDGER,private_ledger)
    atomic_write(state/STATE_QUEUE,queue)
    atomic_write(state/STATE_REVIEWS,updated)
    return {"settled":True,"draft":True,"status":"pending-review",
            "companyId":job["companyId"],"ticker":job["ticker"],"autoApproval":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase",choices=["inspect","reserve","settle"],required=True)
    p.add_argument("--state-dir",required=True,help="Checked-out pulse-data Git worktree")
    p.add_argument("--private-dir",required=True,help="Private runner directory outside repository")
    p.add_argument("--model",default="gpt-6.1-sol")
    args=p.parse_args()
    state=Path(args.state_dir).resolve()
    private=Path(args.private_dir).resolve()
    if state==ROOT or ROOT in state.parents or private==ROOT or ROOT in private.parents:
        raise ValueError("State worktree and private directory must live outside repo")
    if not state.is_dir() or not private.is_dir():raise ValueError("Missing state or private directory")
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    if args.phase=="inspect":
        registry,queue,_=load_context(state)
        result={"status":"preflight-only","queued":sum(j["status"]=="queued" for j in queue["jobs"]),
                "blocked":sum(j["status"]=="blocked" for j in queue["jobs"]),
                "paidAiExecuted":False}
    else:
        if os.getenv("PULSE_PAID_AI_APPROVED")!="YES" or os.getenv("PAID_AI_ENABLED")!="YES":
            raise ValueError("Both explicit owner-activation gates are required for spending workflow")
        if args.phase=="reserve":result=reserve_once(state,private,now,args.model)
        else:result=settle(state,private,now)
    print(json.dumps(result))

if __name__=="__main__":main()
