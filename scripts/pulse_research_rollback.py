"""Stage a version-pointer rollback for owner-reviewed PR, never a direct write."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from pulse_research_release import ROOT,canonical,sha,validate_current_approved

def propose_rollback(approved,company_id,target_id,when):
    current=validate_current_approved(approved)
    if not re.fullmatch(r"research-v:[a-f0-9]{32}",str(target_id)):
        raise ValueError("Invalid target version")
    if company_id not in current["activeByCompany"]:
        raise ValueError("Company has no published sidecar version")
    active_id=current["activeByCompany"][company_id]
    if active_id==target_id:
        raise ValueError("Target already active")
    versions={v["id"]:v for v in current["versions"]}
    if target_id not in versions or versions[target_id]["companyId"]!=company_id:
        raise ValueError("Requested rollback not in this company's immutable archive")
    node=versions[active_id]
    ancestors=set()
    while node.get("parentVersionId"):
        pid=node["parentVersionId"]
        if pid in ancestors or pid not in versions:
            raise ValueError("Cyclic or damaged version history")
        ancestors.add(pid)
        node=versions[pid]
    if target_id not in ancestors:
        raise ValueError("Rollback target must be a verified ancestor, not an unreviewed version")
    when=dt.datetime.fromisoformat(when.replace("Z","+00:00"))
    if when.tzinfo is None:raise ValueError("UTC timestamp required")
    data={**current,"activeByCompany":{**current["activeByCompany"],company_id:target_id}}
    validate_current_approved(data)
    event={"eventType":"rollback-awaiting-owner-pr-merge","companyId":company_id,
           "fromVersion":active_id,"toVersion":target_id,
           "proposedAt":when.astimezone(dt.timezone.utc).isoformat(),
           "actor":"protected-github-review-and-merge-required"}
    event["immutableSha256"]=sha(canonical(event).encode())
    return data,event

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved-index",required=True)
    p.add_argument("--company-id",required=True)
    p.add_argument("--target-version",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    out=Path(a.output).resolve()
    if out==ROOT or out.is_relative_to(ROOT/"public") or out.is_relative_to(ROOT/"src"):
        raise ValueError("Rollback must be staged for a GitHub PR")
    if out.exists() and any(out.iterdir()):raise ValueError("Rollback staging not empty")
    approved=json.loads(Path(a.approved_index).read_text(encoding="utf-8"))
    data,event=propose_rollback(approved,a.company_id,a.target_version,
                               dt.datetime.now(dt.timezone.utc).isoformat())
    target=out/"public/data/approved-research-versions.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    audit=out/"public/data/research-release-audit"/(event["immutableSha256"]+".json")
    audit.parent.mkdir(parents=True,exist_ok=True)
    audit.write_text(json.dumps(event,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"rollbackProposalOnly":True,"from":event["fromVersion"],"to":event["toVersion"],
                      "approvedChangePendingProtectedPRMerge":True}))
if __name__=="__main__":main()
