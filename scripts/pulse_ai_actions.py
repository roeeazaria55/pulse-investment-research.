"""GitHub Actions AI transaction preparation and settlement; NEVER calls OpenAI.

The trusted Actions workflow first commits and pushes an immutable reservation
to pulse-data, then invokes the separately gated private API runner. If the
API call or settlement fails, uncertain reservations remain outstanding for
that report. Other reports can use the remaining budget.

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
from pulse_ai_cost_guard import MODEL_RATES,preflight,reserve,attempt_key,attempt_generation,validate_ledger
from pulse_ai_research_drafts import append_public,build_public_draft,canonical
from run_optional_ai_review import ERROR_REASONS,MAX_OUTPUT_TOKENS,MAX_INPUT_BYTES,prepare

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

def load_context(state,*,include_candidates=True):
    registry=read_json(ROOT/"public/data/official-registry.json")
    queue=validate(read_json(state/STATE_QUEUE),registry)
    if not include_candidates:
        return registry,queue,{}
    candidates=read_json(ROOT/PACKET_CANDIDATES)
    by_id={c["id"]:c for c in candidates["candidates"]}
    return registry,queue,by_id

def recover_interrupted(queue,ledger,now):
    """Called with the shared spending lock, before preparing a new transaction.

    An abandoned runner cannot attest to billing. Legacy holds are linked only
    by an exact, unique ticker and processing timestamp match.
    """
    changed=False
    for job in queue["jobs"]:
        live=job["status"]=="processing"
        incident_hold=job.get("reconciliationHoldId")
        if not live and not (job["status"]=="failed" and incident_hold):
            continue
        same_dispatch = [j for j in queue["jobs"] if j["status"]=="processing"
                         and j["ticker"]==job["ticker"] and j["updatedAt"]==job["updatedAt"]]
        for hold in ledger.get("holds",[]):
            linked = hold.get("jobId")==job["id"]
            legacy = "jobId" not in hold and hold["ticker"]==job["ticker"]
            timestamp_match = live and len(same_dispatch)==1 and utc_at(hold["heldAt"])==job["updatedAt"]
            if (live and linked) or (legacy and (timestamp_match or hold["id"]==incident_hold)):
                hold.update(jobId=job["id"],reconciliation="interrupted-dispatch")
                changed=True
        if live:
            advance(queue,job["id"],"failed",now,actor="trusted-runner")
            job["statusReason"]="billing-reconciliation-required"
            changed=True
    return changed


def record_verified_no_charge(state,hold_id,evidence_ref,now):
    """Prepare an operator-reviewed ledger change; this does not verify billing.

    The reference must identify independently reviewed, attempt-specific evidence
    of zero charge. Never include billing payloads or credentials in pulse-data.
    """
    _,queue,_=load_context(state,include_candidates=False)
    ledger=validate_ledger(read_json(state/STATE_LEDGER))
    hold=next((h for h in ledger.get("holds",[]) if h["id"]==hold_id),None)
    if hold is None:
        raise ValueError("Open reservation not found")
    job=next((j for j in queue["jobs"] if j["ticker"]==hold["ticker"] and (
        j["id"]==hold.get("jobId") or
        ("jobId" not in hold and j.get("reconciliationHoldId")==hold_id)
    )),None)
    if job is None or job["status"] not in {"failed","pending-review"}:
        raise ValueError("Reservation must belong to a reconciliable job")
    closed={**hold,"jobId":job["id"],"evidenceRef":evidence_ref}
    ledger["holds"].remove(hold)
    ledger.setdefault("noCharge",[]).append(closed)
    validate_ledger(ledger)
    requeued=False
    if (job["status"]=="failed" and job["attempts"]<5 and not job["analysisExecuted"]
        and queue["latestByCompany"].get(job["companyId"])==job["id"]
        and not any(h["ticker"]==job["ticker"] for h in ledger["holds"])
        and not any(r.get("jobId")==job["id"] or (
            r["ticker"]==hold["ticker"] and r["packetSha256"]==hold["packetSha256"]
        ) for r in ledger["calls"])):
        advance(queue,job["id"],"queued",now,actor="trusted-runner")
        job["statusReason"]="verified-no-charge-reconciled"
        requeued=True
    atomic_write(state/STATE_LEDGER,ledger)
    if requeued:
        atomic_write(state/STATE_QUEUE,queue)
    return {"recordedNoCharge":True,"requeued":requeued}


def choose(state,model,retry_of=None):
    if model not in MODEL_RATES:raise ValueError("Unsupported model")
    _,queue,candidates=load_context(state)
    ledger=validate_ledger(read_json(state/STATE_LEDGER,optional=True) or {"version":1,"calls":[],"holds":[]})
    receipt = None
    if retry_of:
        receipt = next((r for r in ledger["calls"] if r["id"]==retry_of and "retryOf" not in r), None)
        if receipt is None: raise ValueError("Retry receipt missing or already a retry")
    jobs=sorted((j for j in queue["jobs"] if ((j["status"]=="queued" and not retry_of) or
       (retry_of and j["status"]=="failed" and j.get("statusReason")=="model-output-rejected-after-billing"
        and j["ticker"]==receipt["ticker"]))
       and queue["latestByCompany"].get(j["companyId"])==j["id"]),
       key=lambda j:(j["createdAt"],j["id"]))
    packets=build_all()
    by_job={j["id"]:j for j in queue["jobs"]}
    for j in jobs:
        # A revised candidate may have a new ID for the same earnings report.
        # An unlinked legacy hold blocks only that ticker, since its period is unknown.
        if any(h["ticker"]==j["ticker"] and (
            h.get("jobId") not in by_job or h["jobId"]==j["id"] or
            by_job[h["jobId"]]["reportPeriod"]==j["reportPeriod"]
        ) for h in ledger.get("holds",[])):
            continue
        source=candidates.get(j["candidateId"])
        if (source is None or job_id(source)!=j["id"]
            or source["payloadSha256"]!=j["candidatePayloadSha256"]
            or digest({k:v for k,v in source.items() if k!="payloadSha256"})!=source["payloadSha256"]):
            if retry_of:
                raise ValueError("Candidate changed before queued AI task")
            continue
        packet=packets.get(j["ticker"])
        if packet is None or packet["companyId"]!=j["companyId"]:
            if retry_of:
                raise ValueError("Issuer packet mismatch")
            continue
        supported={ob["sourceSha256"] for ob in packet["financialObservations"]}
        issuer=packet.get("latestIssuerResearch") or {}
        report=issuer.get("report") or {}
        if issuer.get("sourceBoundMetrics"):
            supported.add(report.get("digest"))
        if j["sourceSha256"] not in supported:
            # Do not pay for an unsupported or missing report.
            continue
        if retry_of and (packet["contentSha256"]!=receipt["packetSha256"] or model!=receipt["model"]):
            raise ValueError("Retry source packet/model changed")
        try:
            _,payload=prepare(j["ticker"])
        except (ValueError,KeyError):
            if retry_of:
                raise
            continue
        generation=attempt_generation(ledger,j["ticker"],packet["contentSha256"],model,retry_of)
        key=attempt_key(j["ticker"],packet["contentSha256"],model,retry_of,generation=generation)
        if any(r["id"]==key or (not retry_of and
            r.get("rateRetry") and r["packetSha256"]==packet["contentSha256"]
            and r["ticker"]==j["ticker"] and r["model"]==model
        ) for r in ledger["calls"]):
            continue
        if len(payload.encode("utf-8"))>MAX_INPUT_BYTES:
            continue
        return j,packet,payload
    return None,None,None

def reserve_once(state,private,now,model,retry_of=None,*,allow_rate_retry=False):
    """Prepare worktree files; workflow MUST git push them before a model call."""
    now=utc_at(now)
    _,queue,_=load_context(state)
    ledger=validate_ledger(read_json(state/STATE_LEDGER,optional=True) or {"version":1,"calls":[],"holds":[]})
    recovered=recover_interrupted(queue,ledger,now)
    if recovered:
        atomic_write(state/STATE_LEDGER,ledger)
        atomic_write(state/STATE_QUEUE,queue)
    selected,packet,payload=choose(state,model,retry_of)
    if selected is None:
        return {"ready":False,"changed":recovered,"reason":"no-source-supported-queued-job"}
    dispatch_time=dt.datetime.fromisoformat(now)
    if dispatch_time.strftime("%Y-%m")!=(dispatch_time+dt.timedelta(minutes=15)).strftime("%Y-%m"):
        return {"ready":False,"changed":recovered,"reason":"utc-budget-rollover"}
    input_ceiling=min(100000,len(payload.encode("utf-8"))*2)
    decision=preflight(ledger,selected["ticker"],packet["contentSha256"],model,now,
       input_token_ceiling=input_ceiling,
       output_token_ceiling=MAX_OUTPUT_TOKENS,retry_of=retry_of)
    if not decision["allowed"]:
        if not retry_of and decision["reason"] == "per-call-limit":
            advance(queue,selected["id"],"pending-budget",now,actor="trusted-runner")
            selected["statusReason"]=decision["reason"]
            atomic_write(state/STATE_QUEUE,queue)
            return {"ready":False,"changed":True,"reason":decision["reason"]}
        return {"ready":False,"changed":recovered,"reason":decision["reason"]}
    ledger,hold=reserve(ledger,selected["ticker"],packet["contentSha256"],model,now,
       input_ceiling=input_ceiling,output_ceiling=MAX_OUTPUT_TOKENS,
       retry_of=retry_of,job_id=selected["id"])
    if allow_rate_retry and not retry_of and preflight(
        ledger,selected["ticker"],packet["contentSha256"],model,now,input_ceiling,
        MAX_OUTPUT_TOKENS,rate_retry=True
    )["allowed"]:
        ledger,_=reserve(ledger,selected["ticker"],packet["contentSha256"],model,now,
            input_ceiling,MAX_OUTPUT_TOKENS,job_id=selected["id"],rate_retry=True)
    selected = next(j for j in queue["jobs"] if j["id"]==selected["id"])
    if retry_of: advance(queue,selected["id"],"queued",now,actor="trusted-runner")
    advance(queue,selected["id"],"processing",now,actor="trusted-runner")
    selected["attempts"]+=1
    selected["statusReason"]="precharged-reservation-awaits-api"
    # Both changes will be committed and git-pushed atomically as one commit.
    atomic_write(state/STATE_LEDGER,ledger)
    atomic_write(state/STATE_QUEUE,queue)
    private_write(private/"reservation.json",{
        "jobId":selected["id"],"ticker":selected["ticker"],"model":model,
        "packetSha256":packet["contentSha256"],"heldAt":hold["heldAt"],
        "holdId":hold["id"],"retryOf":retry_of})
    return {"ready":True,"changed":True,"ticker":selected["ticker"],"model":model,
            "jobId":selected["id"],"estimatedMaxUsd":hold["maxUsd"]}

def settle(state,private,now):
    """Persist billed usage and publish only an UNAPPROVED draft. Caller must push."""
    now=utc_at(now)
    reservation=read_json(private/"reservation.json")
    model=reservation["model"]
    registry,queue,_=load_context(state,include_candidates=False)
    job=next((j for j in queue["jobs"] if j["id"]==reservation["jobId"]),None)
    if job is None or job["status"]!="processing" or job["ticker"]!=reservation["ticker"]:
        raise ValueError("Pre-paid queue reservation not current")
    before=validate_ledger(read_json(state/STATE_LEDGER))
    remote_hold=[h for h in before.get("holds",[]) if h["id"]==reservation["holdId"]]
    if (len(remote_hold)!=1 or remote_hold[0]["packetSha256"]!=reservation["packetSha256"]
        or remote_hold[0].get("jobId",job["id"])!=job["id"]):
        raise ValueError("Remote reservation no longer matches")
    private_ledger=validate_ledger(read_json(private/"ledger.json",optional=True) or before)
    slots=[h for h in before.get("holds",[]) if h["id"]==reservation["holdId"] or (
        h.get("rateRetry") and h.get("jobId")==job["id"]
        and h["packetSha256"]==reservation["packetSha256"] and h["model"]==model
    )]
    slot_ids={h["id"] for h in slots}
    receipts=private_ledger["calls"][len(before["calls"]):]
    if (private_ledger["calls"][:len(before["calls"])]!=before["calls"] or len(receipts)>1
        or private_ledger.get("noCharge",[])!=before.get("noCharge",[])):
        raise ValueError("Cost ledger changed during billed analysis")
    billed_ids={r["id"] for r in receipts}
    if not billed_ids<=slot_ids or private_ledger.get("holds",[])!=[
        h for h in before.get("holds",[]) if h["id"] not in billed_ids
    ]:
        raise ValueError("Cost ledger tampering")
    uncertain=[]
    for hold in slots:
        identifier=hold["id"]
        if identifier in billed_ids:
            continue
        if (hold.get("rateRetry") and (private/(identifier+".unused")).is_file()
            and not (private/(identifier+".sent")).exists()):
            # The exclusive dispatcher proved this slot never entered the network.
            private_ledger["holds"].remove(hold)
            continue
        error=private/(identifier+".error")
        reason=error.read_text() if error.is_file() else ""
        if reason not in ERROR_REASONS:
            reason="billing-reconciliation-required"
        next(h for h in private_ledger["holds"] if h["id"]==identifier)["reconciliation"]=reason
        uncertain.append(reason)
    if not receipts:
        advance(queue,job["id"],"failed",now,actor="trusted-runner")
        job["statusReason"]=next((reason for reason in reversed(uncertain) if reason in ERROR_REASONS),
                                "billing-reconciliation-required")
        atomic_write(state/STATE_LEDGER,private_ledger)
        atomic_write(state/STATE_QUEUE,queue)
        return {"settled":False,"draft":False,"status":job["statusReason"]}
    proposal_path=private/"review.json"
    try:
        packet=build_all()[job["ticker"]]
        if packet["contentSha256"]!=reservation["packetSha256"]:
            raise ValueError("Source packet changed after the paid request")
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
    p.add_argument("--phase",choices=["inspect","reserve","settle","record-reviewed-no-charge"],required=True)
    p.add_argument("--state-dir",required=True,help="Checked-out pulse-data Git worktree")
    p.add_argument("--private-dir",required=True,help="Private runner directory outside repository")
    p.add_argument("--model",default="gpt-6.1-sol")
    p.add_argument("--retry-of", default=None)
    p.add_argument("--allow-rate-retry", action="store_true")
    p.add_argument("--hold-id")
    p.add_argument("--evidence-ref")
    args=p.parse_args()
    state=Path(args.state_dir).resolve()
    private=Path(args.private_dir).resolve()
    if state==ROOT or ROOT in state.parents or private==ROOT or ROOT in private.parents:
        raise ValueError("State worktree and private directory must live outside repo")
    if not state.is_dir() or not private.is_dir():raise ValueError("Missing state or private directory")
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    if args.phase=="inspect":
        registry,queue,_=load_context(state,include_candidates=False)
        result={"status":"preflight-only","queued":sum(j["status"]=="queued" for j in queue["jobs"]),
                "blocked":sum(j["status"]=="blocked" for j in queue["jobs"]),
                "paidAiExecuted":False}
    elif args.phase=="record-reviewed-no-charge":
        if not args.hold_id or not args.evidence_ref:
            p.error("An exact hold ID and independently reviewed evidence reference are required")
        result=record_verified_no_charge(state,args.hold_id,args.evidence_ref,now)
    else:
        if os.getenv("PULSE_PAID_AI_APPROVED")!="YES" or os.getenv("PAID_AI_ENABLED")!="YES":
            raise ValueError("Both explicit owner-activation gates are required for spending workflow")
        if args.phase=="reserve":result=reserve_once(state,private,now,args.model,args.retry_of or None,
                                                           allow_rate_retry=args.allow_rate_retry)
        else:result=settle(state,private,now)
    print(json.dumps(result))

if __name__=="__main__":main()
