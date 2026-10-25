"""Build review-only research updates from collected DLO facts and the IREN issuer baseline.

A deterministic metadata/financial-evidence transformation, NOT AI analysis.
Only read public company evidence. No portfolio, API key, valuation or approval writes.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
import json
import math
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/data/latest-research-updates.json"
COMPANIES = {
    "us-dlo-nasdaq-a": "DLO",
    "candidate-iren": "IREN",
    "candidate-nebius": "NBIS",
    "us-smci-nasdaq-common": "SMCI",
}
METRICS = {
    "revenue": "הכנסות",
    "grossProfit": "רווח גולמי",
    "operatingCash": "תזרים תפעולי",
    "capex": "השקעות הוניות",
}
DLO_HOSTS = {"rss.globenewswire.com", "www.globenewswire.com", "dlocal.gcs-web.com"}
IREN_HOSTS = {"iren.gcs-web.com"}
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def trusted_url(url, hosts):
    if not isinstance(url, str):
        return False
    try:
        p = urlparse(url)
        return p.scheme == "https" and p.hostname in hosts and not p.username and not p.password and p.port in (None, 443)
    except ValueError:
        return False


def amount(raw):
    if not isinstance(raw, str) or not re.fullmatch(r"\(?[0-9][0-9,]*(?:\.[0-9]+)?\)?", raw.strip()):
        raise ValueError("Unexpected issuer financial cell")
    negative = raw.startswith("(") and raw.endswith(")")
    value = float(raw.strip("()").replace(",", ""))
    if not math.isfinite(value):
        raise ValueError("Nonfinite issuer financial cell")
    return -value if negative else value


def identity(payload):
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()[:24]


def missing(company, detail):
    return {
        "companyId": company, "ticker": COMPANIES[company], "status": "insufficient-evidence",
        "kind": "no-verified-new-report", "reportPeriod": None, "publishedDate": None,
        "sourceUrl": None, "sourceVersion": None, "metrics": [], "findings": [],
        "questions": [detail], "missing": [detail], "aiAnalysisEnabled": False,
        "reviewRequired": True, "modelChange": "אין שינוי בהנחות או במחירי יעד.",
        "contentId": None,
    }


def dlo_update(observations):
    valid = []
    for r in observations.get("observations", []):
        if not isinstance(r, dict) or r.get("companyId") != "us-dlo-nasdaq-a":
            continue
        value = r.get("value")
        if not (
            r.get("metricId") in METRICS
            and isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            and r.get("unit") == "USD million"
            and r.get("reviewStatus") in ("needs-reconciliation", "pending-review")
            and trusted_url(r.get("sourceUrl"), DLO_HOSTS)
            and isinstance(r.get("sourceSha256"), str) and SHA256.fullmatch(r["sourceSha256"])
            and isinstance(r.get("periodStart"), str) and isinstance(r.get("periodEnd"), str)
            and r["periodStart"] <= r["periodEnd"]
            and isinstance(r.get("basis"), str) and r["basis"].strip()
            and isinstance(r.get("sourceRaw"), str) and r["sourceRaw"].strip()
            and isinstance(r.get("sourceRow"), str) and r["sourceRow"].strip()
        ):
            continue
        valid.append(r)
    if not valid:
        return missing("us-dlo-nasdaq-a", "אין מדדים מחולצים ממקור מאומת מבנית; מצב הדיווח אינו ידוע.")
    # Never silently mix two source versions, even if their dates coincide.
    groups = {}
    for r in valid:
        key = (r["periodEnd"], r["sourceSha256"], r["sourceUrl"])
        groups.setdefault(key, []).append(r)
    key = max(groups, key=lambda k: (k[0], max(str(x.get("collectedAt") or "") for x in groups[k])))
    rows = groups[key]
    seen = set()
    metrics = []
    for r in sorted(rows, key=lambda x: x["metricId"]):
        if r["metricId"] in seen:
            raise ValueError("Duplicate DLO financial metric for a source version")
        seen.add(r["metricId"])
        metrics.append({
            "id": r["metricId"], "label": METRICS[r["metricId"]],
            "value": r["value"], "unit": r["unit"], "periodStart": r["periodStart"],
            "periodEnd": r["periodEnd"], "accountingBasis": r["basis"],
            "sourceRaw": r["sourceRaw"], "sourceRow": r["sourceRow"],
            "sourceUrl": r["sourceUrl"], "reviewStatus": r["reviewStatus"],
            "previousValue": None, "changePercent": None,
            "comparison": "אין נתון קודם מאושר, תואם בתקופה ובהגדרה.",
        })
    warnings = ["ארבעת המדדים, ככל שנמצאו, ממתינים לבדיקת אנליסט; אין השוואה לתחזית שנוצרה לאחר תאריך פרסום הדוח."]
    if any(r["reviewStatus"] == "needs-reconciliation" for r in rows):
        warnings.insert(0, "גרסת המקור דורשת בירור (needs-reconciliation); הנתונים אינם מאושרים.")
    if len(groups) > 1:
        warnings.append("קיימות גרסאות מקור/תקופות נוספות. מוצגת גרסה אחת בלבד, ללא איחוד ביניהן.")
    body = {
        "companyId": "us-dlo-nasdaq-a", "ticker": "DLO",
        "status": "needs-reconciliation" if any(r["reviewStatus"] == "needs-reconciliation" for r in rows) else "pending-review",
        "kind": "automatically-extracted-issuer-data",
        "reportPeriod": rows[0].get("period") or f'{rows[0]["periodStart"]}/{rows[0]["periodEnd"]}',
        "publishedDate": rows[0].get("publishedDate"), "sourceUrl": key[2],
        "sourceVersion": key[1], "metrics": metrics,
        "findings": ["המערכת חילצה נתוני מקור מדוח DLO; לא נקבע שינוי בתזת ההשקעה.",
                     "לא זוהתה הפתעת תחזית: דוח Q2 קדם לתחזיות PULSE שנשמרו באוקטובר."],
        "questions": ["האם הגדרות IFRS, ה־CAPEX ותזרים המזומנים תואמות למודל ולדוח המקורי?"],
        "missing": warnings, "aiAnalysisEnabled": False, "reviewRequired": True,
        "modelChange": "אין שינוי במחיר יעד או בהסתברויות Bear/Base/Bull.",
    }
    body["contentId"] = identity(body)
    return body


def iren_update(source):
    company = "candidate-iren"
    if source.get("companyId") != company or not trusted_url(source.get("sourceUrl"), IREN_HOSTS):
        return missing(company, "קישור או שיוך מקור IREN אינו תקין.")
    if source.get("reviewStatus") != "pending-analyst-review":
        return missing(company, "מצב ביקורת מקור IREN בלתי צפוי.")
    operations = next((t for t in source.get("tables", []) if t.get("statement") == "Consolidated Statement of Operations"), None)
    cash = next((t for t in source.get("tables", []) if t.get("statement") == "Consolidated Statement of Cashflows"), None)
    if not operations or not cash or any(t.get("unit") != "US$m" or t.get("periodKind") != "Year ended" or t.get("periodEnd") != "June 30, 2026" or t.get("priorPeriodEnd") != "June 30, 2025" for t in (operations, cash)):
        return missing(company, "כותרות טבלאות IREN השתנו; השוואה שנתית נחסמה.")
    def row(table, label):
        matches = [r for r in table.get("rows", []) if r.get("label") == label]
        if len(matches) != 1:
            raise ValueError("Missing or duplicated IREN source row: " + label)
        return amount(matches[0]["current"]), amount(matches[0]["prior"])
    revenue = row(operations, "Total Revenue")
    operating = row(cash, "Net cash from (used in) operating activities")
    cash_ppe = row(cash, "Payments for property, plant and equipment net of computer hardware")
    hardware = row(cash, "Payments for computer hardware")
    cash_capex = (-(cash_ppe[0] + hardware[0]), -(cash_ppe[1] + hardware[1]))
    raw_metrics = [
        ("revenue", revenue, "consolidated revenue (GAAP)", "Total Revenue"),
        ("operatingCash", operating, "reported cash from operations including customer advances", "Net cash from (used in) operating activities"),
        ("capex", cash_capex, "calculated cash payments for PPE and computer hardware only", "PPE cash payments + computer hardware cash payments"),
    ]
    metrics = []
    for metric_id, (current, previous), basis, source_row in raw_metrics:
        pct = round((current - previous) / abs(previous) * 100, 2) if previous != 0 else None
        metrics.append({
            "id": metric_id, "label": METRICS[metric_id], "value": round(current, 6),
            "previousValue": round(previous, 6), "changePercent": pct,
            "unit": "USD million", "periodStart": "2025-07-01", "periodEnd": "2026-06-30",
            "accountingBasis": basis, "sourceRaw": "curated issuer FY2026 vs FY2025 table cells",
            "sourceRow": source_row, "sourceUrl": source["sourceUrl"],
            "reviewStatus": "pending-review",
            "comparison": "FY2026 מול FY2025 באותה שורת מקור. שינוי היסטורי, לא הפתעה ביחס לתחזית PULSE.",
        })
    body = {
        "companyId": company, "ticker": "IREN", "status": "historical-baseline-pending-review",
        "kind": "bounded-curated-issuer-table-extract", "reportPeriod": "FY2026",
        "publishedDate": source.get("publishedDate"), "sourceUrl": source["sourceUrl"],
        "sourceVersion": identity(source), "metrics": metrics,
        "findings": ["קיימת השוואה שנתית FY2026/FY2025 לשלוש קבוצות מדדים מתוך טבלאות המנפיק.",
                     "הדוח פורסם לפני מחקר PULSE באוקטובר; השינוי השנתי אינו הפתעה ואינו מחייב שינוי מודל."],
        "questions": ["מהו תזרים המזומנים המתוקנן ללא מקדמות לקוחות?",
                      "איך ממומנות השקעות GPU ו־PPE והאם קיימות השקעות נוספות מחוץ לסעיפים שנמדדו?"],
        "missing": ["תמצית מקור מוגבלת ולא סריקה חיה של הדוח האחרון.",
                    "ה־CAPEX כולל שני סעיפי תשלום מזומן בלבד; אינו כלל ההשקעות.",
                    "מדדי התזרים מושפעים ממקדמות; הנתונים טרם אושרו על ידי אנליסט."],
        "aiAnalysisEnabled": False, "reviewRequired": True,
        "modelChange": "אין שינוי במחיר יעד, בתחזיות או בהסתברויות Bear/Base/Bull.",
    }
    body["contentId"] = identity(body)
    return body


def build(observations, iren_source):
    reports = [
        dlo_update(observations),
        iren_update(iren_source),
        missing("candidate-nebius", "לא קיימת קליטה אוטומטית מאושרת חדשה לצורך עדכון המחקר של NBIS."),
        missing("us-smci-nasdaq-common", "לא קיימת קליטה אוטומטית מאושרת חדשה לצורך עדכון המחקר של SMCI."),
    ]
    return {
        "version": 1, "generatedAt": datetime.now(timezone.utc).isoformat(),
        "reports": reports, "aiStatus": "not-enabled",
        "notice": "Deterministic review-only research. Curated IREN FY2026 baseline is not fresh collection. No AI run, auto-approval, price-target change or historical forecast surprise.",
    }


def main():
    observations = load(ROOT / "public/data/auto-financial-observations.json")
    iren = load(ROOT / "public/data/iren-fy26-source.json")
    data = build(observations, iren)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUT)
    print(json.dumps({"companies": len(data["reports"]),
                      "withMetrics": [r["ticker"] for r in data["reports"] if r["metrics"]],
                      "ai": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
