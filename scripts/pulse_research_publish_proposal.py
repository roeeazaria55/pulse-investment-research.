"""Stage active research archive update for a SECOND authenticated GitHub PR.

A merged review-proposal PR is not the approved model. A second protected
human-reviewed merge is the sole authority to advance the canonical active
research version index. Neither step can be invoked from untrusted web JSON.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

from pulse_research_release import ROOT,canonical,sha,validate_current_approved,SAFE_ROOT

def prepare_publication(proposal,old_index,proposal_pdf_bytes):
    if (not isinstance(proposal,dict) or proposal.get("proposalOnly") is not True
        or proposal.get("simulation") is not False
        or proposal.get("publishAutomatically") is not False
        or proposal.get("releaseAuthority")!="human-protected-github-pr-merge-required"):
        raise ValueError("Approval is unavailable for mock or self-approved research")
    old=validate_current_approved(old_index)
    source=proposal.get("candidateVersion")
    if not isinstance(source,dict) or source.get("publicationStatus")!="proposed-awaiting-authenticated-merge":
        raise ValueError("Missing unapproved, verified research proposal")
    body={k:v for k,v in source.items() if k!="immutableSha256"}
    if source.get("immutableSha256")!=sha(canonical(body).encode()):
        raise ValueError("Proposed version metadata was edited")
    if (not isinstance(proposal_pdf_bytes,bytes) or not proposal_pdf_bytes.startswith(b"%PDF-")
        or sha(proposal_pdf_bytes)!=source["pdfSha256"]
        or len(proposal_pdf_bytes)!=source["pdfBytes"] or source["pdfPages"]<1):
        raise ValueError("PDF digest/size mismatch: do not publish")
    if proposal.get("pdfSha256")!=source["pdfSha256"]:
        raise ValueError("Proposal digest disagrees with PDF")
    if not re.fullmatch(r"research-v:[a-f0-9]{32}",source["id"]):
        raise ValueError("Malformed proposal version")
    prior=old["activeByCompany"].get(source["companyId"])
    if prior!=source.get("parentVersionId"):
        raise ValueError("Research changed since proposal; fresh review required")
    if any(v["id"]==source["id"] for v in old["versions"]):
        raise ValueError("Already published: cannot overwrite")
    if (not isinstance(source.get("pdfPath"),str) or
        not source["pdfPath"].startswith(SAFE_ROOT+"/") or
        ".." in Path(source["pdfPath"]).parts):
        raise ValueError("Unsafe approved version path")
    # No new prices, scenarios, inputs, or PDF replacements are created here.
    # These would require explicit source-cited quantitative review in a
    # later owner-reviewed model-change PR, not a model's proposed JSON.
    if (source.get("approvedTargetChanged") is not False or
        source.get("approvedScenarioWeightsChanged") is not False):
        raise ValueError("Automated target/weights change forbidden")
    published={**source,
        "publicationStatus":"approved-upon-protected-pr-merge",
        "approvalMethod":"independent-human-github-pr-review-and-merge",
        "approvalProvenance":"GitHub repository merged PR audit log",
        "approvalTimestamp":None,
        "sourceProposalVersionSha256":source["immutableSha256"],
    }
    published.pop("immutableSha256")
    published["immutableSha256"]=sha(canonical(published).encode())
    updated={"version":1,
             "versions":[*old["versions"],published],
             "activeByCompany":{**old["activeByCompany"],source["companyId"]:source["id"]}}
    validate_current_approved(updated)
    return updated,published

def stage_publication(*,proposal_path,approved_path,pdf_path,outdir):
    p=Path(proposal_path)
    proposal=json.loads(p.read_text(encoding="utf-8"))
    current=Path(approved_path)
    old=json.loads(current.read_text(encoding="utf-8")) if current.exists() else {
        "version":1,"versions":[],"activeByCompany":{}}
    data=Path(pdf_path).read_bytes()
    index,version=prepare_publication(proposal,old,data)
    out=Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Publication preview directory must be empty")
    target=out/version["pdfPath"]
    if target.exists():raise ValueError("Cannot overwrite an existing PDF")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    meta=out/"public/data/approved-research-versions.json"
    meta.parent.mkdir(parents=True,exist_ok=True)
    meta.write_text(json.dumps(index,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return {"publicationProposalId":version["id"],"sourceSha256":version["sourcePacketSha256"],
            "approvedPointerChangeIsStillPendingPRMerge":True,"pdfPath":version["pdfPath"],
            "pdfSha256":version["pdfSha256"],"automaticPriceTargetChange":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--proposal",required=True)
    ap.add_argument("--proposal-pdf",required=True)
    ap.add_argument("--approved-index",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    out=Path(a.output).resolve()
    if out==ROOT or out.is_relative_to(ROOT/"public") or out.is_relative_to(ROOT/"src"):
        raise ValueError("Cannot modify approved data directly; stage for protected PR review")
    result=stage_publication(proposal_path=a.proposal,approved_path=a.approved_index,
                             pdf_path=a.proposal_pdf,outdir=out)
    print(json.dumps(result))
if __name__=="__main__":main()
