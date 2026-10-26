"""Deterministic Hebrew accounting readout, no AI and no model mutation.

Never infer 'beat/miss' from YoY comparatives. Margins require identical
issuer, source, currency, current AND prior periods and positive revenue.
"""
from __future__ import annotations
import math


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def source_margins(metrics):
    if not isinstance(metrics, list):
        raise ValueError("Malformed source metrics")
    by_id = {x.get("id"): x for x in metrics if isinstance(x, dict)}
    rev = by_id.get("revenue")
    if not rev:
        return []
    results = []
    for key, label, question in [
        ("grossProfit", "שיעור רווח גולמי",
         "האם הנחת שיעור הרווח הגולמי במודל משתמשת באותה הגדרה חשבונאית ובאותה תקופה?"),
        ("operatingIncome", "שיעור רווח תפעולי",
         "האם הוצאות התפעול וקצב ההתרחבות תואמים את הנחת שיעור הרווח התפעולי במודל?"),
    ]:
        profit=by_id.get(key)
        if not profit:
            continue
        if not (rev.get("unit") == profit.get("unit")
            and rev.get("sourceUrl") == profit.get("sourceUrl")
            and rev.get("sourceSha256") == profit.get("sourceSha256")
            and rev.get("reportId") == profit.get("reportId")
            and all(rev.get(k) == profit.get(k) and rev.get(k) is not None for k in (
                 "periodStart", "periodEnd", "previousPeriodStart", "previousPeriodEnd"))
            and all(m.get("reviewStatus") == "pending-review" for m in (rev, profit))
            and all(_finite(v) for v in (rev.get("value"),rev.get("previousValue"),
                         profit.get("value"),profit.get("previousValue")))
            and rev["value"]>0 and rev["previousValue"]>0):
            continue
        current = 100*profit["value"]/rev["value"]
        previous = 100*profit["previousValue"]/rev["previousValue"]
        if not all(map(math.isfinite,(current,previous))) or abs(current)>10000 or abs(previous)>10000:
            continue
        delta=current-previous
        trend="עלה" if delta>0.005 else "ירד" if delta<-0.005 else "נותר דומה"
        results.append({
            "metricId":key,"label":label,
            "currentMarginPercent":round(current,2),
            "previousMarginPercent":round(previous,2),
            "changePercentagePoints":round(delta,2),
            "periodStart":rev["periodStart"],"periodEnd":rev["periodEnd"],
            "priorPeriodStart":rev["previousPeriodStart"],
            "priorPeriodEnd":rev["previousPeriodEnd"],
            "unit":"percent","sourceUrl":rev["sourceUrl"],
            "sourceSha256":rev["sourceSha256"],
            "reviewStatus":"pending-review",
            "finding":f"{label} {trend}: {current:.2f}% לעומת {previous:.2f}% בתקופה המקבילה ({delta:+.2f} נקודות אחוז). נתון לחקר, לא תחזית ולא שינוי מחיר יעד.",
            "question":question,
            "type":"period-matched-derived-margin",
            "modelEligible":False,
        })
    return results
