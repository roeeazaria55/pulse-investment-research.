"""Offline review-decision proposals for PR-gated financial source observations.

Security: this CLI does NOT authenticate analysts and does NOT approve changes
in a public browser. Reviewer identity is authenticated by GitHub permissions
and the PR review/merge process. An approval ledger is trusted ONLY after a
maintainer merges its reviewed PR.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

ALLOWED = {"approved", "rejected", "needs-reconciliation"}
VERSION = 1


def apply_review(request, snapshot, ledger, now):
    if not isinstance(snapshot, dict) or snapshot.get("version") != 1 or not isinstance(snapshot.get("observations"), list):
        raise ValueError("Invalid automatic-observation source snapshot")
    if not isinstance(ledger, dict) or ledger.get("version", 1) != 1:
        raise ValueError("Invalid existing review ledger")
    if not isinstance(request, dict):
        raise ValueError("Invalid review decision")
    required = ("observationId", "reviewVersionId", "sourceSha256", "decision", "reason", "evidenceUrl")
    if any(not isinstance(request.get(k), str) or not request[k].strip() for k in required):
        raise ValueError("Missing review identity, reason or evidence")
    if request["decision"] not in ALLOWED:
        raise ValueError("Unknown review decision")
    if not request["evidenceUrl"].startswith("https://"):
        raise ValueError("Review evidence must be an HTTPS link")
    matching = [o for o in snapshot["observations"] if isinstance(o, dict) and o.get("id") == request["observationId"]]
    if len(matching) != 1:
        raise ValueError("Observation identity is missing or ambiguous")
    observation = matching[0]
    if observation.get("reviewVersionId") != request["reviewVersionId"] or observation.get("sourceSha256") != request["sourceSha256"]:
        raise ValueError("Source document version does not match reviewed observation")
    if observation.get("reviewStatus") not in ("pending-review", "needs-reconciliation"):
        raise ValueError("Unexpected upstream review state")
    if request["decision"] == "approved":
        if observation.get("reviewStatus") != "pending-review" or observation.get("revisedSource"):
            raise ValueError("A revised or conflicting source requires reconciliation, not automatic approval")
        if not isinstance(observation.get("value"), (float,int)) or not math.isfinite(observation["value"]):
            raise ValueError("Invalid financial value")
        for k in ("companyId", "metricId", "periodStart", "periodEnd", "sourceUrl", "sourceRaw", "basis", "unit"):
            if not isinstance(observation.get(k), str) or not observation[k]:
                raise ValueError("Approved observation lacks auditable accounting metadata: "+k)
        if not observation["sourceUrl"].startswith("https://"):
            raise ValueError("Issuer evidence URL must be HTTPS")
    if not isinstance(now, str):
        raise ValueError("Missing decision timestamp")
    try:
        dt.datetime.fromisoformat(now.replace("Z","+00:00"))
    except ValueError:
        raise ValueError("Invalid decision timestamp")
    fingerprint = hashlib.sha256((request["observationId"]+"|"+request["decision"]+"|"+request["reason"]+"|"+request["evidenceUrl"]).encode()).hexdigest()
    events = list(ledger.get("decisions", []))
    if any(e.get("fingerprint") == fingerprint for e in events):
        return {"version":VERSION,"decisions":events,"notice":"Decisions require authenticated GitHub PR review and merge."}, False
    # Never overwrite an earlier decision; a new decision is a new event.
    events.append({
        "fingerprint":fingerprint, "observationId":observation["id"],
        "companyId":observation["companyId"], "metricId":observation["metricId"],
        "reviewVersionId":observation["reviewVersionId"], "sourceSha256":observation["sourceSha256"],
        "sourceUrl":observation["sourceUrl"], "periodStart":observation["periodStart"],
        "periodEnd":observation["periodEnd"], "value":observation["value"],
        "unit":observation["unit"], "basis":observation["basis"],
        "decision":request["decision"], "reason":request["reason"],
        "evidenceUrl":request["evidenceUrl"], "proposedAt":now,
        "authentication":"GitHub PR merge required; proposedAt is not proof of actor identity",
    })
    return {"version":VERSION,"decisions":events,"notice":"Decisions require authenticated GitHub PR review and merge."}, True


def main():
    parser=argparse.ArgumentParser(description="Generate a financial decision ledger change for manual GitHub PR review")
    parser.add_argument("--request",required=True,help="Locally prepared JSON review request; never an untrusted report body")
    parser.add_argument("--snapshot",default="public/data/auto-financial-observations.json")
    parser.add_argument("--ledger",default="public/data/financial-review-ledger.json")
    args=parser.parse_args()
    request=json.loads(Path(args.request).read_text())
    snapshot=json.loads(Path(args.snapshot).read_text())
    dest=Path(args.ledger)
    current=json.loads(dest.read_text()) if dest.exists() else {"version":1,"decisions":[]}
    new,changed=apply_review(request,snapshot,current,dt.datetime.now(dt.timezone.utc).isoformat())
    if not changed:
        print("Already proposed: no changes")
        return
    temp=dest.with_suffix(".json.tmp")
    temp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
    temp.replace(dest)
    print("Review decision recorded in a local file; submit via GitHub PR. No public approval was performed.")


if __name__=="__main__":
    main()
