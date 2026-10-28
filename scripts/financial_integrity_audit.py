"""Read-only financial integrity audit. Does not approve observations or publish data."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
from pathlib import Path
from urllib.parse import urlparse

def valid_day(s):
    if not isinstance(s,str):
        return False
    try:
        return dt.date.fromisoformat(s).isoformat()==s
    except ValueError:
        return False

def audit(snapshot,registry):
    allowed={c["id"]:set(c.get("allowedHosts",[])) for c in registry.get("companies",[])}
    reports=snapshot.get("reports",[])
    errors=[];warnings=[];rows=[];seen=set()
    for report in reports:
        company=report.get("companyId")
        if company not in allowed or company in seen:
            errors.append(f"unknown or duplicate company: {company}")
            continue
        seen.add(company)
        metrics=report.get("metrics",[])
        status=report.get("status")
        source=report.get("sourceUrl")
        digest=report.get("sourceVersion")
        if status=="insufficient-evidence" and (metrics or source or digest):
            errors.append(f"{company}: source-free report contains evidence")
        if metrics and (not source or not isinstance(digest,str) or len(digest)!=64):
            errors.append(f"{company}: missing source identity")
        if source:
            parsed=urlparse(source)
            if parsed.scheme!="https" or parsed.hostname not in allowed[company] or parsed.username or parsed.password:
                errors.append(f"{company}: unapproved source host")
        metric_ids=set()
        for metric in metrics:
            name=metric.get("id")
            if name in metric_ids:
                errors.append(f"{company}: duplicate metric {name}")
            metric_ids.add(name)
            n=metric.get("value")
            if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n):
                errors.append(f"{company}/{name}: invalid value")
            if metric.get("sourceUrl")!=source:
                errors.append(f"{company}/{name}: source differs from report")
            start,end=metric.get("periodStart"),metric.get("periodEnd")
            if not valid_day(start) or not valid_day(end) or start>end:
                errors.append(f"{company}/{name}: invalid accounting period")
            if metric.get("reviewStatus") not in ("pending-review","needs-reconciliation"):
                errors.append(f"{company}/{name}: unexpected analyst approval claim")
            previous=metric.get("previousValue")
            previous_start=metric.get("previousPeriodStart")
            previous_end=metric.get("previousPeriodEnd")
            if previous is not None and (isinstance(previous,bool) or not isinstance(previous,(int,float)) or not math.isfinite(previous)):
                errors.append(f"{company}/{name}: invalid prior number")
            if previous is not None and (not valid_day(previous_start) or not valid_day(previous_end)):
                warnings.append(f"{company}/{name}: prior period cannot be verified; suppress comparative insight")
            if company=="us-dlo-nasdaq-a" and (previous is not None or metric.get("changePercent") is not None):
                errors.append("DLO: unreconciled historical comparison")
        if status=="needs-reconciliation":
            warnings.append(f"{company}: reconciliation still pending")
        if status=="historical-baseline-pending-review":
            warnings.append(f"{company}: historical baseline, not latest release")
        if not metrics:
            warnings.append(f"{company}: no supported metrics")
        rows.append({"companyId":company,"ticker":report.get("ticker"),"status":status,
                     "metricCount":len(metrics),"reportPeriod":report.get("reportPeriod"),
                     "publishedDate":report.get("publishedDate"),"sourceUrl":source,
                     "sourceDigest":digest,"analystApproved":False})
    for company in allowed.keys()-seen:
        errors.append(f"missing company: {company}")
    return {"version":1,"safe":not errors,"companyCount":len(rows),
            "financialMetricCompanies":sum(bool(r["metricCount"]) for r in rows),
            "metricCount":sum(r["metricCount"] for r in rows),"companies":rows,
            "errors":errors,"warnings":warnings,
            "notice":"Technical consistency audit only; all observations require analyst review."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--latest",default="public/data/latest-research-updates.json")
    parser.add_argument("--registry",default="public/data/official-registry.json")
    parser.add_argument("--output",default="work/financial-integrity-audit.json")
    args=parser.parse_args()
    snapshot=json.loads(Path(args.latest).read_text(encoding="utf-8"))
    registry=json.loads(Path(args.registry).read_text(encoding="utf-8"))
    outcome=audit(snapshot,registry)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:outcome[k] for k in ("safe","companyCount","metricCount","errors","warnings")},ensure_ascii=False))
    if not outcome["safe"]:
        raise SystemExit(1)

if __name__=="__main__": main()
