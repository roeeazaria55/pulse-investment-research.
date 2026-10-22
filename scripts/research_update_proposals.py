"""Evidence-only research update briefs; not investment advice or AI-generated claims."""
import hashlib
import json
from pathlib import Path

REVIEW_TASKS={
 "revenue":"השווה לתקופה קודמת רק אם קיימים נתוני GAAP/IFRS תואמים; בחן מנועי צמיחה.",
 "grossProfit":"בדוק מרווחים, עלויות עיבוד ושינויים בתמהיל, ללא הסקת מסקנות מהנתון הבודד.",
 "operatingCash":"בדוק הון חוזר, תזמון סליקה ותשלומים; אין להסיק מכאן FCF.",
 "capex":"בדוק הגדרת הוצאות ההשקעה, רכוש קבוע ונכסים בלתי מוחשיים.",
}
def build_proposals(snapshot,comparison,ledger):
    by_source={}
    for ob in snapshot.get("observations",[]):
        if not isinstance(ob,dict) or ob.get("metricId") not in REVIEW_TASKS or not ob.get("sourceSha256"):
            continue
        key=(ob.get("companyId"),ob.get("reviewVersionId"))
        by_source.setdefault(key,[]).append(ob)
    match={r.get("observationId"):r for r in comparison.get("results",[]) if isinstance(r,dict)}
    decisions={}
    for d in ledger.get("decisions",[]):
        if isinstance(d,dict):decisions[d.get("observationId")]=d
    proposals=[]
    for (company_id,review_id),rows in by_source.items():
        rows=sorted(rows,key=lambda x:x["metricId"])
        source=rows[0]
        evidence=[]
        for ob in rows:
            d=decisions.get(ob.get("id"))
            approved=bool(d and d.get("decision")=="approved" and d.get("sourceSha256")==ob.get("sourceSha256"))
            match_status=match.get(ob.get("id"),{}).get("status")
            evidence.append({
                "observationId":ob.get("id"),"metricId":ob["metricId"],"value":ob.get("value"),
                "unit":ob.get("unit"),"raw":ob.get("sourceRaw"),"periodStart":ob.get("periodStart"),
                "periodEnd":ob.get("periodEnd"),"basis":ob.get("basis"),
                "sourceSha256":ob.get("sourceSha256"),"sourceUrl":ob.get("sourceUrl"),
                "approvalStatus":"approved" if approved else ob.get("reviewStatus","pending-review"),
                "forecastComparisonStatus":match_status or "no-comparable-forecast",
                "reviewQuestion":REVIEW_TASKS[ob["metricId"]],
            })
        ident="research-proposal:"+hashlib.sha256((str(company_id)+"|"+str(review_id)).encode()).hexdigest()[:32]
        proposals.append({
            "id":ident,"companyId":company_id,"reviewVersionId":review_id,
            "sourceUrl":source.get("sourceUrl"),"reportPublishedDate":source.get("publishedDate"),
            "period":source.get("period"),"evidence":evidence,
            "status":"review-only",
            "thesisImpact":"לא נקבע — יש לבדוק את הנתונים והמקורות לפני הסקת השפעה על תזת ההשקעה.",
            "valuationAction":"אין שינוי במחיר יעד, בתחזיות או בהסתברויות Bear/Base/Bull.",
            "aiAnalysisEnabled":False,
            "missing":["אישור מקור וגרסה","השוואה מאושרת לתקופה קודמת","ניתוח השפעה על ההנחות במודל"],
        })
    return {"version":1,"proposals":sorted(proposals,key=lambda p:p["id"]),
            "notice":"Deterministic source-based briefing, NOT AI narrative. No approved thesis or valuation mutation."}

def main():
    root=Path("public/data")
    snap=json.loads((root/"auto-financial-observations.json").read_text())
    path=root/"forecast-actual-comparisons.json"
    comparisons=json.loads(path.read_text()) if path.exists() else {}
    ledger_path=root/"financial-review-ledger.json"
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    data=build_proposals(snap,comparisons,ledger)
    dest=root/"research-update-proposals.json"
    temp=dest.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    temp.replace(dest)
    print(json.dumps({"proposals":len(data["proposals"]),"ai":False}))

if __name__=="__main__":main()
