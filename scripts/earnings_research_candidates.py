"""Append-only, source-bound earnings research candidates. Never approves or publishes a valuation."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/"public/data/earnings-research-candidates.json"

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def valid_day(raw):
    try:
        return isinstance(raw,str) and dt.date.fromisoformat(raw).isoformat()==raw
    except ValueError:
        return False

def source_allowed(url,company):
    if not isinstance(url,str):
        return False
    try:
        u=urlsplit(url)
        return (u.scheme=="https" and u.hostname in company.get("allowedHosts",[])
                and not u.username and not u.password and u.port is None
                and not any(ord(ch)<32 for ch in url))
    except ValueError:
        return False

def comparable(metric):
    prev=metric.get("previousValue")
    current=metric.get("value")
    if (not isinstance(prev,(int,float)) or isinstance(prev,bool)
            or not isinstance(current,(int,float)) or isinstance(current,bool)
            or not math.isfinite(prev) or not math.isfinite(current)):
        return False
    dates=[metric.get(k) for k in ("periodStart","periodEnd","previousPeriodStart","previousPeriodEnd")]
    if not all(valid_day(d) for d in dates):
        return False
    a,b,c,d=(dt.date.fromisoformat(x) for x in dates)
    if not (a<=b and c<=d and d<b):
        return False
    # As-of balance values are comparable at their two actual dates, not as flows.
    return (a==b and c==d) or (a!=b and c!=d and (b-a).days==(d-c).days)

def metric_evidence(row,company,source,source_hash):
    if (row.get("reviewStatus") not in ("pending-review","needs-reconciliation")
            or row.get("sourceUrl")!=source or not source_allowed(row.get("sourceUrl"),company)
            or not isinstance(row.get("id"),str) or not isinstance(row.get("label"),str)):
        return None
    value=row.get("value")
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
        return None
    if not valid_day(row.get("periodStart")) or not valid_day(row.get("periodEnd")):
        return None
    eligible=comparable(row) and company["id"]!="us-dlo-nasdaq-a"
    prior=row.get("previousValue") if eligible else None
    difference=round(value-prior,6) if eligible else None
    percent=(round((value-prior)/prev*100,2) if eligible and (prev:=prior)>0 and value>=0
             and row.get("unit")!="percent" else None)
    return {"id":row["id"],"label":row["label"],"value":value,
            "unit":row.get("unit"),"periodStart":row["periodStart"],"periodEnd":row["periodEnd"],
            "previousValue":prior,"previousPeriodStart":row.get("previousPeriodStart") if eligible else None,
            "previousPeriodEnd":row.get("previousPeriodEnd") if eligible else None,
            "absoluteChange":difference,"percentChange":percent,
            "comparisonStatus":"historical-arithmetic-review-only" if eligible else "blocked-incomparable-or-unreconciled",
            "sourceUrl":source,"sourceSha256":source_hash,"accountingBasis":row.get("accountingBasis"),
            "reviewStatus":row.get("reviewStatus")}

def build(latest,previous,registry,monitors,now):
    if (latest.get("version")!=1 or previous.get("version",1)!=1 or
            not isinstance(latest.get("reports"),list) or not isinstance(previous.get("candidates",[]),list) or
            not isinstance(registry.get("companies"),list)):
        raise ValueError("Malformed research candidate input")
    companies={c["id"]:c for c in registry["companies"]}
    if len(companies)!=12 or len(latest["reports"])!=12 or len({r.get("companyId") for r in latest["reports"]})!=12:
        raise ValueError("Expected twelve unique issuer reports")
    saved={}
    for row in previous.get("candidates",[]):
        if (not isinstance(row,dict) or not isinstance(row.get("id"),str)
                or row["id"] in saved or row.get("companyId") not in companies
                or row.get("publicationStatus")!="not-approved"
                or row.get("modelChange")!="none"
                or not isinstance(row.get("payloadSha256"),str)
                or row["payloadSha256"]!=digest({k:v for k,v in row.items() if k!="payloadSha256"})):
            raise ValueError("Invalid or mutable previous candidate")
        saved[row["id"]]=row
    new=0
    seen={}
    for report in latest["reports"]:
        cid=report["companyId"]
        company=companies.get(cid)
        if not company: raise ValueError("Unknown issuer")
        source=report.get("sourceUrl")
        version=report.get("sourceVersion")
        if source is None or version is None:
            if report.get("metrics"):
                raise ValueError("Financial facts without bound report source")
            continue  # No attested report bytes; never invent a new filing.
        if not (source_allowed(source,company) and isinstance(version,str)
                and len(version)==64 and all(ch in "0123456789abcdef" for ch in version)):
            raise ValueError("Unapproved or malformed report identity")
        evidence=report.get("reportEvidence")
        if evidence and (evidence.get("url")!=source or evidence.get("sha256")!=version):
            raise ValueError("Document evidence identity differs from mapped report")
        metrics=report.get("metrics",[])
        if not isinstance(metrics,list): raise ValueError("Malformed report metrics")
        items=[metric_evidence(m,company,source,version) for m in metrics]
        if any(m is None for m in items):raise ValueError("Metric provenance or dates invalid")
        if len({m["id"] for m in items})!=len(items):
            raise ValueError("Duplicate issuer metric")
        support=[m for m in monitors if m.get("companyId")==cid]
        questions=[]
        if len(support)>1:raise ValueError("Duplicate monitoring model")
        for m in (support[0].get("metrics",[]) if support else []):
            if m.get("id") in {o["id"] for o in items}:
                questions.append({"metricId":m["id"],"nextCheck":str(m.get("nextCheck") or "")[:700],
                                  "thesisRisk":str(m.get("thesisRisk") or "")[:700],
                                  "baseline":str(m.get("baseline") or "")[:500]})
        # Hash binds the new research candidate to exactly one retained report/version.
        identity={"companyId":cid,"sourceVersion":version,"sourceUrl":source,
                  "reportPeriod":report.get("reportPeriod"),"contentId":report.get("contentId")}
        ident="earnings-candidate:"+digest(identity)[:32]
        if ident not in saved:
            status="needs-review" if items and report.get("status") not in ("needs-reconciliation","insufficient-evidence") else "blocked"
            saved[ident]={
                "id":ident,"companyId":cid,"ticker":report.get("ticker") or company.get("ticker") or cid,
                "sourceUrl":source,"sourceSha256":version,"reportPeriod":report.get("reportPeriod"),
                "publishedDate":report.get("publishedDate") if valid_day(report.get("publishedDate")) else None,
                "firstCandidateAt":now,"status":status,"publicationStatus":"not-approved",
                "provenanceStatus":"retained-source-provisional", "metrics":items,
                "analystReviewQuestions":questions,
                "summary":"טיוטת ראיות מספריות לבדיקת אנליסט; אינה מחקר השקעה מאושר או ניתוח AI.",
                "thesisImpact":"לא נקבע. יש לבחון את ההנחות וסיכוני החברה מול הראיות החדשות.",
                "scenarioReview":{"status":"not-calculated","bear":None,"base":None,"bull":None,
                                  "reason":"לא חושבו משקולות או מחירי יעד ללא נתוני מודל מאושרים ותהליך ביקורת."},
                "forecastComparisonStatus":"not-approved-or-proven-comparable",
                "modelChange":"none","aiAnalysisExecuted":False,
                "sourceResearchContentId":report.get("contentId"),
                "limitations":list(report.get("missing",[]))[:10],
            }
            saved[ident]["payloadSha256"]=digest(saved[ident])
            new+=1
        seen[cid]=ident
    return {"version":1,"updatedAt":now if new or not previous.get("updatedAt") else previous["updatedAt"],
            "candidates":sorted(saved.values(),key=lambda x:(x["companyId"],x["firstCandidateAt"],x["id"])),
            "latestByCompany":seen,"newCandidateCount":new,
            "notice":"Evidence-only immutable drafts. No analyst approval, automatic AI review, target or probability changes."}

def main():
    latest=json.loads((ROOT/"public/data/latest-research-updates.json").read_text(encoding="utf-8"))
    registry=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))
    monitors=json.loads((ROOT/"src/data/thesisMonitoring.json").read_text(encoding="utf-8"))
    old=json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    result=build(latest,old,registry,monitors,dt.datetime.now(dt.timezone.utc).isoformat())
    if old!=result:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        tmp=OUTPUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        tmp.replace(OUTPUT)
    print(json.dumps({"total":len(result["candidates"]),"new":result["newCandidateCount"],
                      "current":len(result["latestByCompany"]),"approved":0}))

if __name__=="__main__":
    main()
