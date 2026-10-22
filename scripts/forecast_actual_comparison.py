"""Date-safe finance forecast vs actual comparison; no inferred historical truth."""
import datetime as dt
import json
import math
from pathlib import Path

def calendar_date(iso):
    try:return dt.date.fromisoformat(iso)
    except (TypeError,ValueError):return None

def compare(forecast,actual,decisions,*,verified_review_authority=False):
    reasons=[]
    if forecast.get("companyId")!=actual.get("companyId"):
        reasons.append("company mismatch")
    if forecast.get("metricId")!=actual.get("metricId"):
        reasons.append("metric mismatch")
    point=forecast.get("point",{})
    if point.get("period")!=actual.get("period"):
        reasons.append("period mismatch: no annualization or YTD substitution")
    if point.get("unit")!=actual.get("unit"):
        reasons.append("unit mismatch: no unreviewed conversion")
    if point.get("basis")!=actual.get("basis"):
        reasons.append("accounting-definition mismatch")
    # A recordDate is the conservative, verified boundary; a user-supplied
    # researchAsOf is never used as proof of a pre-publication forecast.
    first=calendar_date((forecast.get("firstRecordedAt") or "")[:10])
    published=calendar_date(actual.get("publishedDate"))
    if first is None or published is None or first>=published:
        reasons.append("forecast was not demonstrably archived before result publication")
    current_approvals=[e for e in decisions if
                       e.get("observationId")==actual.get("id") and
                       e.get("sourceSha256")==actual.get("sourceSha256")]
    if not current_approvals or current_approvals[-1].get("decision")!="approved":
        reasons.append("observation is not approved by a merged analyst review")
    # A mutable public ledger is not evidence of a verified review. Main currently
    # has no protected-branch policy. The production pipeline MUST NOT set this
    # flag until a server-side reviewer-authentication gate has been implemented.
    if not verified_review_authority:
        reasons.append("Review Decision Recorded; analyst approval is not verified by an enforced repository policy")
    val=point.get("value"); actual_val=actual.get("value")
    if isinstance(val,bool) or isinstance(actual_val,bool) or not isinstance(val,(float,int)) or not isinstance(actual_val,(float,int)) or not math.isfinite(val) or not math.isfinite(actual_val):
        reasons.append("invalid numeric value")
    if reasons:
        return {"status":"blocked","reasons":reasons,"difference":None,"percent":None}
    difference=actual_val-val
    return {"status":"comparable","reasons":[],"difference":round(difference,6),
            "percent":None if val==0 else round(difference/abs(val)*100,6)}

def evaluate(forecast_archive,actuals,ledger):
    results=[]
    for a in actuals.get("observations",[]):
        for f in forecast_archive.get("forecasts",[]):
            if f.get("companyId")!=a.get("companyId") or f.get("metricId")!=a.get("metricId"):
                continue
            results.append({"forecastId":f.get("id"),"observationId":a.get("id"),
                            **compare(f,a,ledger.get("decisions",[]))})
    return {"version":1,"results":results,
            "notice":"No backtesting with unverified research timestamps; differences only for source-approved prospective measurements."}

def main():
    root=Path("public/data")
    archive=json.loads((root/"forecast-archive.json").read_text())
    actual=json.loads((root/"auto-financial-observations.json").read_text())
    decisions=root/"financial-review-ledger.json"
    ledger=json.loads(decisions.read_text()) if decisions.exists() else {"version":1,"decisions":[]}
    data=evaluate(archive,actual,ledger)
    out=root/"forecast-actual-comparisons.json"
    tmp=out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    tmp.replace(out)
    print(json.dumps({"comparisons":len(data["results"]),"valid":sum(x["status"]=="comparable" for x in data["results"])}))

if __name__=="__main__":main()
