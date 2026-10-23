"""Evidence-only research update briefs; not investment advice or AI-generated claims."""
import hashlib
import json
from pathlib import Path
from report_review_queue import version_id

REVIEW_TASKS={
 "revenue":"השווה לתקופה קודמת רק אם קיימים נתוני GAAP/IFRS תואמים; בחן מנועי צמיחה.",
 "grossProfit":"בדוק מרווחים, עלויות עיבוד ושינויים בתמהיל, ללא הסקת מסקנות מהנתון הבודד.",
 "operatingCash":"בדוק הון חוזר, תזמון סליקה ותשלומים; אין להסיק מכאן FCF.",
 "capex":"בדוק הגדרת הוצאות ההשקעה, רכוש קבוע ונכסים בלתי מוחשיים.",
}
def build_proposals(snapshot, comparison, ledger):
    """Build a review-only briefing; mutable ledger/compare files grant no authority.

    The issuer document and digest must identify a *single* source version.
    Conflicting observations fail closed instead of mixing unrelated evidence
    into one apparently coherent analyst briefing.
    """
    by_source = {}
    source_identity = {}
    observations = snapshot.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("Invalid financial observation snapshot")
    seen_observations = set()
    for ob in observations:
        if not isinstance(ob, dict):
            raise ValueError("Malformed financial observation")
        if ob.get("metricId") not in REVIEW_TASKS:
            continue
        required = ("id", "companyId", "reviewVersionId", "reportId",
                    "sourceSha256", "sourceUrl", "period", "reviewStatus")
        if any(not isinstance(ob.get(field), str) or not ob[field]
               for field in required):
            raise ValueError("Incomplete research evidence identity")
        if (len(ob["sourceSha256"]) != 64 or
                any(c not in "0123456789abcdef" for c in ob["sourceSha256"])):
            raise ValueError("Invalid research evidence digest")
        if ob["reviewStatus"] not in ("pending-review", "needs-reconciliation"):
            raise ValueError("Unverified research evidence must not claim approval")
        expected = version_id(ob["companyId"], ob["reportId"], ob["sourceSha256"])
        if ob["reviewVersionId"] != expected:
            raise ValueError("Research evidence review version does not match source digest")
        if ob["id"] in seen_observations:
            raise ValueError("Duplicate research observation identity")
        seen_observations.add(ob["id"])
        key = (ob["companyId"], ob["reviewVersionId"])
        identity = (ob["reportId"], ob["sourceSha256"], ob["sourceUrl"], ob["period"])
        if key in source_identity and source_identity[key] != identity:
            raise ValueError("Conflicting issuer evidence grouped under one review version")
        source_identity[key] = identity
        by_source.setdefault(key, []).append(ob)

    # Comparisons from the mutable data branch are display hints only. A
    # 'comparable' status cannot confer a verified analyst approval here.
    raw_results = comparison.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Invalid comparison result snapshot")
    matches = {}
    for r in raw_results:
        if not isinstance(r, dict):
            raise ValueError("Malformed comparison result")
        ident = r.get("observationId")
        if not isinstance(ident, str):
            raise ValueError("Comparison missing observation identity")
        matches.setdefault(ident, []).append(r)

    proposals = []
    for (company_id, review_id), rows in by_source.items():
        rows = sorted(rows, key=lambda x: x["metricId"])
        source = rows[0]
        evidence = []
        for ob in rows:
            comparisons = matches.get(ob["id"], [])
            if not comparisons:
                match_status, match_reasons = "no-comparable-forecast", []
            else:
                match_status = "blocked"
                match_reasons = []
                for record in comparisons:
                    if record.get("status") == "blocked" and isinstance(record.get("reasons"), list):
                        match_reasons.extend(
                            reason[:240] for reason in record["reasons"][:20]
                            if isinstance(reason, str)
                        )
                    else:
                        match_reasons.append(
                            "Unverified comparison status cannot establish an approved forecast result"
                        )
                if not match_reasons:
                    match_reasons = ["Comparison requires verified analyst review"]
            evidence.append({
                "observationId": ob["id"], "metricId": ob["metricId"], "value": ob.get("value"),
                "unit": ob.get("unit"), "raw": ob.get("sourceRaw"),
                "periodStart": ob.get("periodStart"), "periodEnd": ob.get("periodEnd"),
                "basis": ob.get("basis"), "sourceSha256": ob["sourceSha256"],
                "sourceUrl": ob["sourceUrl"],
                # A recorded decision is NOT authenticated. Never promote a
                # pending or reconciliation observation from a public ledger.
                "approvalStatus": ob["reviewStatus"],
                "forecastComparisonStatus": match_status,
                "forecastComparisonReasons": match_reasons[:40],
                "reviewQuestion": REVIEW_TASKS[ob["metricId"]],
            })
        ident = "research-proposal:" + hashlib.sha256(
            (str(company_id) + "|" + str(review_id)).encode()
        ).hexdigest()[:32]
        proposals.append({
            "id": ident, "companyId": company_id, "reviewVersionId": review_id,
            "sourceUrl": source["sourceUrl"],
            "reportPublishedDate": source.get("publishedDate"),
            "period": source["period"], "evidence": evidence,
            "status": "review-only",
            "thesisImpact": "לא נקבע — יש לבדוק את הנתונים והמקורות לפני הסקת השפעה על תזת ההשקעה.",
            "valuationAction": "אין שינוי במחיר יעד, בתחזיות או בהסתברויות Bear/Base/Bull.",
            "aiAnalysisEnabled": False,
            "missing": ["אישור מקור וגרסה", "השוואה מאושרת לתקופה קודמת",
                        "ניתוח השפעה על ההנחות במודל"],
        })
    return {"version": 1, "proposals": sorted(proposals, key=lambda p: p["id"]),
            "notice": "Deterministic source-based briefing, NOT AI narrative. No approved thesis or valuation mutation."}

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
