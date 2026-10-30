"""Prepare public, unapproved AI research drafts from validated private model outputs.

This module never calls OpenAI, never approves analyst research, never modifies
active valuations/PDFs, and never copies the original source packet into public/.
Model execution attestation must come from the invoking trusted runner; a JSON
field alone is never proof of execution.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path

from ai_analyst_review_contract import validate_ai_proposal
from pulse_ai_cost_guard import MODEL_RATES

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)

def build_public_draft(packet,proposal,model,*,execution_attested=False):
    if execution_attested is not True:
        raise ValueError("Trusted execution attestation required; never accept self-claimed model execution")
    if model not in MODEL_RATES:
        raise ValueError("Unknown model provenance")
    valid=validate_ai_proposal(packet,proposal,model_execution_attested=True)
    source_hash=packet["contentSha256"]
    review_hash=hashlib.sha256(canonical(proposal).encode("utf-8")).hexdigest()
    return {
        "version":1,
        "id":"ai-draft:"+hashlib.sha256((packet["companyId"]+"|"+source_hash+"|"+review_hash).encode()).hexdigest()[:32],
        "companyId":packet["companyId"],
        "ticker":packet["ticker"],
        "status":"requires-human-review",
        "analysisMode":"model-generated-unverified",
        "reviewStatus":"not-approved",
        "publicationStatus":"not-approved",
        "sourcePacketSha256":source_hash,
        "model":model,
        "proposalSha256":review_hash,
        "evidenceCitations":proposal["evidenceCitations"],
        "interpretations":proposal["interpretations"],
        "analystQuestions":proposal["analystQuestions"],
        "suggestedScenarioReview":proposal["suggestedScenarioReview"],
        "proposedValuationAction":"no-automatic-change",
        "approvedTargetPrice":None,
        "approvedScenarios":None,
        "sourceUrl":None,
        "notice":"AI interpretation, unverified; citations refer to pre-reviewed context. Source verification and analyst approval are required before publication.",
        "citationCount":valid["cited"]
    }

def append_public(previous, draft, now):
    if not isinstance(previous,dict) or previous.get("version",1)!=1 or not isinstance(previous.get("drafts",[]),list):
        raise ValueError("Invalid draft history")
    dt.datetime.fromisoformat(now.replace("Z","+00:00"))
    saved={}
    for entry in previous.get("drafts",[]):
        if not isinstance(entry,dict) or not isinstance(entry.get("id"),str) or entry["id"] in saved:
            raise ValueError("Invalid/duplicate previous draft")
        if entry.get("publicationStatus")!="not-approved" or entry.get("proposedValuationAction")!="no-automatic-change":
            raise ValueError("Unexpected approved model mutation")
        # Integrity digest detects edits to previously stored review drafts.
        recorded=entry.get("immutableSha256")
        body={k:v for k,v in entry.items() if k!="immutableSha256"}
        if recorded!=hashlib.sha256(canonical(body).encode()).hexdigest():
            raise ValueError("Existing AI research draft was modified")
        saved[entry["id"]]=entry
    if draft["id"] not in saved:
        row={**draft,"firstRecordedAt":now}
        row["immutableSha256"]=hashlib.sha256(canonical(row).encode()).hexdigest()
        saved[draft["id"]]=row
        added=1
    else:
        added=0
    return {"version":1,
            "updatedAt":now if added else previous.get("updatedAt",now),
            "drafts":sorted(saved.values(),key=lambda x:(x["companyId"],x["firstRecordedAt"],x["id"])),
            "newDraftCount":added}

def main():
    import argparse
    p=argparse.ArgumentParser(description="Transform externally verified model call into unapproved AI research draft")
    p.add_argument("--packet",required=True)
    p.add_argument("--private-proposal",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--model",choices=sorted(MODEL_RATES),required=True)
    p.add_argument("--model-execution-attested",action="store_true")
    a=p.parse_args()
    # Requiring explicit attestation is useful for integration tests, but manual
    # invocation alone cannot establish model provenance. Never treat as approval.
    packet=json.loads(Path(a.packet).read_text(encoding="utf-8"))
    proposed=json.loads(Path(a.private_proposal).read_text(encoding="utf-8"))
    draft=build_public_draft(packet,proposed,a.model,execution_attested=a.model_execution_attested)
    output=Path(a.output)
    if output.suffix!=".json" or "public/data" not in str(output):
        raise ValueError("Destination must be explicit public/data JSON draft store")
    previous=json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
    result=append_public(previous,draft,dt.datetime.now(dt.timezone.utc).isoformat())
    temp=output.with_suffix(".json.tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    temp.replace(output)
    print(json.dumps({"status":"unapproved-review-draft-exported","ticker":packet["ticker"],
                      "newDraftCount":result["newDraftCount"],"approvedModelChanges":0}))

if __name__=="__main__": main()
