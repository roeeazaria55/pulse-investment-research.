"""Build source-backed review-only updates for the entire 12-company PULSE registry.

A deterministic metadata/financial-evidence transformation, NOT AI analysis.
Only read public company evidence. No portfolio, API key, valuation or approval writes.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
from issuer_coverage import build as build_coverage
from financial_readout import source_margins
import json
import math
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/data/latest-research-updates.json"
COMPANIES = {
    company["id"]: company.get("label") or company.get("ticker") or company["name"]
    for company in json.loads((ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))["companies"]
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



def model_context(report):
    """Compare issuer observations with the *existing* dated PULSE research and
    base-scenario assumptions. Distinct accounting periods/definitions must
    NEVER be labeled forecast beats or misses."""
    company = report["companyId"]
    if company not in ("us-dlo-nasdaq-a", "candidate-iren"):
        return report
    ticker = COMPANIES[company].lower()
    model = load(ROOT / "src/data/models" / (ticker + ".json"))
    research = load(ROOT / "src/data/research" / (ticker + ".json"))["analysis"]
    if model.get("companyId") != company or research.get("companyId") != company:
        raise ValueError("Issuer research/model identity mismatch")
    base_rows = [x for x in model["scenarios"] if x.get("id") == "base"]
    if len(base_rows) != 1:
        raise ValueError("Missing or duplicate base-scenario valuation")
    base = base_rows[0]["inputs"]
    supplied = [x for x in load(ROOT / "src/data/suppliedResearch.json")
                if x.get("companyId") == company]
    if len(supplied) > 1:
        raise ValueError("Duplicate primary supplied valuation for issuer")
    primary = supplied[0] if supplied else None
    if primary:
        scenarios = [x for x in primary.get("scenarios", []) if x.get("id") == "base"]
        if len(scenarios) != 1 or primary.get("method") != "stated":
            raise ValueError("Unsupported supplied primary valuation shape")
        weight = scenarios[0].get("weight")
        target = scenarios[0].get("statedValue")
        if not isinstance(weight, (int, float)) or not isinstance(target, (int, float)):
            raise ValueError("Malformed supplied primary scenario")
        if not all(math.isfinite(v) for v in (weight, target)) or not 0 <= weight <= 100:
            raise ValueError("Nonfinite supplied primary scenario")
        report["activeValuationContext"] = {
            "status": "unverified-supplied-research", "scenario": "base",
            "baseTargetPerShare": target, "weight": weight, "currency": "USD",
            "asOf": primary["date"], "source": "src/data/suppliedResearch.json",
            "pdfFilename": primary["filename"],
            "isComparableFinancialActual": False,
            "note": "מחקר שסופק ידנית והוא התצוגה הראשית; מחירי יעד אינם נתוני חברה מאומתים. מודל JSON הישן הוא ארכיון ואינו מחליף את המחקר שסופק."
        }
    else:
        report["activeValuationContext"] = {
            "status": "existing-quantified-scenario-model", "scenario": "base",
            "baseTargetPerShare": None, "weight": base_rows[0]["probability"],
            "currency": model["quoteCurrency"], "asOf": model["analysisDate"],
            "source": "src/data/models/" + ticker + ".json", "pdfFilename": None,
            "isComparableFinancialActual": False,
            "note": "תנאי מודל הבסיס נבחנים לתקופה ולהגדרה אך אינם עדכון שווי אוטומטי."
        }
    mapping = {
        "us-dlo-nasdaq-a": {
            "grossProfit": ("driver", "רווח גולמי שנתי בתחזית 2027",
                            "רבעון Q2 2026 מול שנת 2027; אין להשוות מספרית לשנה או להסיק הפתעת תחזית.",
                            "יש לבדוק GP/TPV ברבעונים הבאים ואת הרווח התפעולי לפני שינוי שיעור המרה ומכפיל."),
            "revenue": (None, "הכנסות Q2 במחקר קודם",
                        "בדיקת התאמה לערך 399.7 במחקר שסופק; מקור המחקר אינו ראיה עצמאית.",
                        "אין שינוי תזה מוכח; דרושה בדיקת מכירות ורווח גולמי מאושרות."),
        },
        "candidate-iren": {
            "revenue": ("revenue", "תחזית הכנסות לשנה הקלנדרית 2027",
                        "FY2026 שהסתיימה ביוני מול שנת 2027 קלנדרית; תקופות שונות.",
                        "יש לעקוב אחר קצב הכנסות AI מוכרות, מסירות וקצב הפעלה; לא להתייחס ל־ARR כהכנסות."),
            "operatingCash": ("operatingCash", "תחזית תזרים מיולי 2026 עד אוקטובר 2027",
                              "FY2026 לפני התקופה במודל; התזרים המדווח כולל מקדמות לקוחות לעומת גישור נפרד במודל.",
                              "נדרש גישור מקדמות, מימון, ריבית ותזרים מתוקנן."),
            "capex": ("capex", "תחזית CAPEX ביולי 2026 עד אוקטובר 2027",
                      "FY2026 ושני סעיפי מזומן בלבד, לעומת CAPEX רחב ותקופה עתידית במודל.",
                      "לבדוק תשלומי GPU, התחייבויות ופיקדונות מחוץ לשני סעיפי המזומן."),
        },
    }
    comparisons = []
    for metric in report["metrics"]:
        info = mapping.get(company, {}).get(metric["id"])
        if not info:
            continue
        input_key, label, reason, implication = info
        current_assumption = base.get(input_key) if input_key else None
        if input_key and (isinstance(current_assumption, bool) or
                          not isinstance(current_assumption, (float, int)) or
                          not math.isfinite(current_assumption)):
            raise ValueError("Malformed base scenario " + input_key)
        # DLO contemporaneous supplied analyst baseline must match exactly to
        # be labeled a research-text match; no data scraped from prose as truth.
        text_match = None
        if company == "us-dlo-nasdaq-a" and metric["id"] in ("revenue", "grossProfit"):
            expected = {"revenue": 399.7, "grossProfit": 127.2}[metric["id"]]
            text_match = str(expected) in research["fields"]["revenue"] and abs(metric["value"] - expected) < 1e-8
        comparisons.append({
            "metricId": metric["id"], "status": "not-comparable-period-or-definition",
            "modelScenario": "base" if input_key else None,
            "modelStatus": "archived-secondary" if primary else "existing-quantified-scenario-model",
            "modelInput": input_key, "modelValue": current_assumption,
            "modelUnit": "USD million" if input_key else None,
            "modelPeriod": "calendar-2027" if input_key == "revenue" or company == "us-dlo-nasdaq-a" and input_key == "driver"
                           else "2026-07-01/2027-10-19" if input_key else None,
            "modelLabel": label, "modelAsOf": model["analysisDate"],
            "modelSource": "src/data/models/" + ticker + ".json",
            "researchAsOf": research["asOf"],
            "researchSource": "src/data/research/" + ticker + ".json",
            "researchTextMatch": text_match,
            "reason": reason, "analystReview": implication,
            "automaticChange": False,
        })
    report["modelReview"] = comparisons
    report["findings"].append("נבדקו המחקר הראשי, מודל הבסיס ותקופות המקור. אין מדידה תואמת שניתן לפרש כהפתעת תחזית.")
    report["missing"].append("השוואות אלה הן בדיקת התאמה בין מקורות והנחות — לא תחזית חדשה ולא אישור לנתוני המקור.")
    report["contentId"] = identity({k: v for k, v in report.items() if k != "contentId"})
    return report

def missing(company, detail):
    return {
        "companyId": company, "ticker": COMPANIES[company], "status": "insufficient-evidence",
        "kind": "no-verified-new-report", "reportPeriod": None, "publishedDate": None,
        "sourceUrl": None, "sourceVersion": None, "sourceDigestKind": None, "metrics": [], "findings": [],
        "questions": [detail], "missing": [detail], "modelReview": [], "aiAnalysisEnabled": False,
        "reviewRequired": True, "modelChange": "אין שינוי בהנחות או במחירי יעד.",
        "contentId": None,
    }


def dlo_update(observations):
    # Bind each extracted observation to the actual retained issuer report.
    # A syntactically valid digest alone is NOT proof that a source exists.
    documents = load(ROOT / "public/data/report-intake.json")["documents"]
    issuer_docs = {(d.get("id"), d.get("sha256")): d for d in documents
                   if isinstance(d, dict) and d.get("companyId") == "us-dlo-nasdaq-a"
                   and d.get("status") == "extracted"}
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
        source_doc = issuer_docs.get((r.get("reportId"), r["sourceSha256"]))
        if not source_doc or r["sourceUrl"] != source_doc.get("url") or r.get("publishedDate") != source_doc.get("publishedDate"):
            continue
        if bool(source_doc.get("revised")) and r["reviewStatus"] != "needs-reconciliation":
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
            "sourceRaw": r["sourceRaw"], "sourceRow": r["sourceRow"], "sourcePreviousRaw": None,
            "sourcePage": None, "sourceDocumentUrl": None,
            "sourceUrl": r["sourceUrl"], "reviewStatus": r["reviewStatus"],
            "previousValue": None, "changePercent": None,
            "comparison": "אין נתון קודם מאושר, תואם בתקופה ובהגדרה.",
        })
    # Optional issuer KPI rows from the SAME retained digest selected above.
    doc = issuer_docs.get((rows[0].get("reportId"), key[1]))
    if doc:
        tables = [t for t in doc.get("tables", []) if t.get("rows", [])[:3] == [
            ["", "Three months ended on June 30", "Six months ended on June 30"],
            ["", "2026", "2025", "% change", "2026", "2025", "% change"],
            ["Key Performance metrics", "(In millions of US$ except for %)"]]]
        if len(tables) == 1:
            for source, mid, label, basis in [
                ("TPV", "tpv", "היקף תשלומים TPV", "Issuer TPV operational KPI; not IFRS revenue"),
                ("Net Income", "netIncome", "רווח נקי", "Issuer performance summary net income, rounded USD million")]:
                lines=[r for r in tables[0]["rows"] if r and r[0]==source]
                if len(lines)!=1 or len(lines[0])!=7:continue
                try: value=amount(lines[0][1])
                except ValueError:continue
                metrics.append({**metrics[0], "id":mid, "label":label, "value":value,
                    "accountingBasis":basis, "sourceRow":source,
                    "sourceRaw":lines[0][1], "sourcePreviousRaw":None,
                    "periodStart":"2026-04-01", "periodEnd":"2026-06-30",
                    "previousValue":None, "changePercent":None,
                    "reviewStatus":"needs-reconciliation" if any(r["reviewStatus"]=="needs-reconciliation" for r in rows) else "pending-review"})
    warnings = ["המדדים שנמצאו, ממתינים לבדיקת אנליסט; אין השוואה לתחזית שנוצרה לאחר תאריך פרסום הדוח."]
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
        "sourceVersion": key[1], "sourceDigestKind": "retained-issuer-html-sha256", "metrics": metrics,
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
    if cash_capex[0] < 0 or cash_capex[1] < 0:
        raise ValueError("Unexpected CAPEX cash sign")
    cell_raw = {m["label"]: m for t in (operations, cash) for m in t["rows"]}
    if not trusted_url(source.get("pdfUrl"), IREN_HOSTS):
        return missing(company, "כתובת מסמך IREN PDF אינה תואמת למנפיק.")
    raw_metrics = [
        ("revenue", revenue, "consolidated revenue (GAAP)", "Total Revenue"),
        ("operatingCash", operating, "reported cash from operations including customer advances", "Net cash from (used in) operating activities"),
        ("capex", cash_capex, "calculated cash payments for PPE and computer hardware only", "PPE cash payments + computer hardware cash payments"),
    ]
    metrics = []
    for metric_id, (current, previous), basis, source_row in raw_metrics:
        pct = round((current - previous) / abs(previous) * 100, 2) if previous != 0 else None
        if metric_id == "capex":
            raw_current = cell_raw["Payments for property, plant and equipment net of computer hardware"]["current"] + " + " + cell_raw["Payments for computer hardware"]["current"]
            raw_previous = cell_raw["Payments for property, plant and equipment net of computer hardware"]["prior"] + " + " + cell_raw["Payments for computer hardware"]["prior"]
            pdf_page = cash["pdfPage"]
        else:
            raw_current = cell_raw[source_row]["current"]
            raw_previous = cell_raw[source_row]["prior"]
            pdf_page = operations["pdfPage"] if metric_id == "revenue" else cash["pdfPage"]
        if not isinstance(pdf_page, int) or not 1 <= pdf_page <= 100:
            raise ValueError("Malformed issuer source PDF page")
        metrics.append({
            "id": metric_id, "label": METRICS[metric_id], "value": round(current, 6),
            "previousValue": round(previous, 6), "changePercent": pct,
            "unit": "USD million", "periodStart": "2025-07-01", "periodEnd": "2026-06-30",
            "previousPeriodStart": "2024-07-01", "previousPeriodEnd": "2025-06-30",
            "accountingBasis": basis, "sourceRaw": raw_current,
            "sourcePreviousRaw": raw_previous, "sourcePage": pdf_page,
            "sourceDocumentUrl": source["pdfUrl"],
            "sourceRow": source_row, "sourceUrl": source["sourceUrl"],
            "reviewStatus": "pending-review",
            "comparison": "FY2026 מול FY2025 באותה שורת מקור. שינוי היסטורי, לא הפתעה ביחס לתחזית PULSE.",
        })
    body = {
        "companyId": company, "ticker": "IREN", "status": "historical-baseline-pending-review",
        "kind": "bounded-curated-issuer-table-extract", "reportPeriod": "FY2026",
        "publishedDate": source.get("publishedDate"), "sourceUrl": source["sourceUrl"],
        "sourceVersion": sha256(json.dumps(source,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest(),
        "sourceDigestKind": "curated-extract-json-sha256-not-original-pdf", "metrics": metrics,
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



def other_issuer_update(row):
    """A source document is a finding, never an approved financial observation.

    Only uniquely scoped, same-unit XBRL duration facts from retained SEC
    documents may appear as typed *proposals*. All other parsed tables are
    visible through the original document link but remain unparsed.
    """
    company = row["companyId"]
    if company == "us-dlo-nasdaq-a":
        raise ValueError("Dedicated issuer cannot use generic fallback")
    evidence = row.get("report")
    metrics = row.get("typedMetrics", [])
    if not evidence or not metrics:
        text = ("דוח שמור זמין לקריאה, אך טרם זוהו מדדים מחולצים שאפשר לאמת בהגדרה ובתקופה."
                if evidence else "טרם נשמר דוח רשמי קריא לצורך חילוץ מדדים פיננסיים.")
        entry = missing(company, text)
        entry["questions"] = row.get("analystQuestions", []) or [text]
        entry["reportEvidence"] = evidence
        entry["intakeStatus"] = row["intakeStatus"]
        return entry
    source = evidence["url"]
    version = evidence["sha256"]
    if not (SHA256.fullmatch(version) and all(m["sourceUrl"] == source and
            m["sourceSha256"] == version and m["reportId"] == evidence["id"] and
            m["reviewStatus"] == "pending-review" and (m["unit"] == "USD million" or (company == "candidate-gilat-telecom" and m["unit"] == "ILS million") or (company == "us-lmnd-nyse-common" and m["id"] == "grossLossRatio" and m["unit"] == "percent")) for m in metrics)):
        raise ValueError("Inconsistent cross-source issuer XBRL evidence")
    allowed = {c["id"]: set(c["allowedHosts"]) for c in load(ROOT / "public/data/official-registry.json")["companies"]}
    if not trusted_url(source, allowed[company]):
        raise ValueError("Report link not on the registered issuer domain")
    margins = source_margins(metrics)
    body = {
        "companyId": company, "ticker": COMPANIES[company],
        "status": "historical-baseline-pending-review" if company == "candidate-iren" else "pending-review", "kind": ("issuer-original-table-review-only" if metrics[0]["evidenceScope"] in ("retained-issuer-html-table","retained-issuer-pdf-table") else "structured-sec-xbrl-review-only"),
        "reportPeriod": evidence.get("documentPeriod") or metrics[0]["periodStart"] + "/" + metrics[0]["periodEnd"],
        "publishedDate": evidence.get("publishedDate"), "sourceUrl": source,
        "sourceVersion": version,
        "sourceDigestKind": ("retained-issuer-pdf-table-sha256" if metrics[0]["evidenceScope"]=="retained-issuer-pdf-table"
                                 else "retained-issuer-html-table-sha256" if metrics[0]["evidenceScope"]=="retained-issuer-html-table"
                                 else "retained-sec-companyfacts-json-sha256" if metrics[0]["evidenceScope"]=="retained-sec-companyfacts-xbrl"
                                 else "retained-sec-inline-xbrl-sha256"),
        "metrics": [{k: v for k, v in metric.items() if k not in (
             "sourceSha256", "reportId", "evidenceScope", "sourceContext")}
             for metric in metrics],
        "modelReview": [],
        "findings": ["נתונים פיננסיים חולצו משורות מקור מובְנות; התקופות, ההגדרות וההשפעה על המודל עדיין ממתינות לבדיקת אנליסט."] + [m["finding"] for m in margins],
        "questions": (row.get("analystQuestions", []) or ["האם התקופה והיחידה תואמות למודל?"]) + [m["question"] for m in margins],
        "missing": ["לא הושוו ביצועים לתחזית מתוארכת; אין אישור אוטומטי או שינוי במחיר יעד.",
                    "הצלחת קליטת המקור בהווה תלויה במצב הורדת הדוח המוצג בנפרד."] +
                   (["נשמרו גם מסמכים ללא מיפוי פיננסי. מוצגת התקופה האחרונה שחולצה, ולא בהכרח הדוח האחרון שפורסם."] if row.get("unmappedDocumentCount") else []),
        "aiAnalysisEnabled": False, "reviewRequired": True,
        "modelChange": "אין שינוי בתרחישים, בהנחות או במחירי יעד.",
        "reportEvidence": evidence, "intakeStatus": row["intakeStatus"],
    }
    body["contentId"] = identity({k:v for k,v in body.items() if k not in ("reportEvidence", "intakeStatus")})
    return body


def source_check_summary(source_inventory):
    """Source *index* polling health. Does not certify financial extraction."""
    if source_inventory is None:
        return {}
    rows = source_inventory.get("sources")
    if not isinstance(rows, list):
        raise ValueError("Malformed official source inventory")
    result = {}
    for company in COMPANIES:
        entries = [r for r in rows if isinstance(r, dict) and r.get("companyId") == company]
        statuses = [r.get("status") for r in entries]
        if any(status not in ("ok", "failed", "partial", "no-change", "skipped") for status in statuses):
            raise ValueError("Unknown issuer polling status")
        success = sum(status in ("ok", "no-change") for status in statuses)
        failures = sum(status in ("failed", "partial") for status in statuses)
        overall = ("unconfigured" if not entries else
                   "partial" if success and failures else
                   "failed" if failures else "ok" if success else "not-checked")
        attempts = [v for r in entries if isinstance((v := r.get("lastAttemptAt")), str) and v]
        successful = [v for r in entries if isinstance((v := r.get("lastSuccessfulAt")), str) and v]
        result[company] = {
            "status": overall, "sourcesConfigured": len(entries),
            "sourcesHealthy": success, "sourcesFailed": failures,
            "lastAttemptAt": max(attempts, default=None),
            "lastSuccessfulAt": max(successful, default=None),
            "note": "Issuer source-index polling only, not confirmation of a new or approved financial report.",
        }
    return result


def build(observations, iren_source, source_inventory=None, coverage=None):
    if coverage is None:
        coverage = build_coverage(load(ROOT / "public/data/official-registry.json"),
                                  load(ROOT / "public/data/report-intake.json"))
    rows = coverage.get("coverage", [])
    if len(rows) != len(COMPANIES) or {r["companyId"] for r in rows} != set(COMPANIES):
        raise ValueError("12-company official evidence coverage is incomplete")
    indexed = {r["companyId"]: r for r in rows}
    reports = []
    for company in COMPANIES:
        row = indexed[company]
        if company == "us-dlo-nasdaq-a":
            report = model_context(dlo_update(observations))
        elif company == "candidate-iren":
            report = model_context(other_issuer_update(row) if row.get("typedMetrics") else iren_update(iren_source))
        else:
            report = other_issuer_update(row)
        report.setdefault("reportEvidence", row.get("report"))
        report.setdefault("intakeStatus", row["intakeStatus"])
        report["intakeAttemptAt"] = row.get("intakeAttemptAt")
        report["intakeSuccessAt"] = row.get("intakeSuccessAt")
        report["intakeError"] = (row.get("lastError") or "")[:180] or None
        report["issuerPortal"] = row.get("issuerPortal")
        report["analystQuestions"] = row.get("analystQuestions", [])
        reports.append(report)
    return {
        "version": 1, "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceChecks": source_check_summary(source_inventory),
        "reports": reports, "aiStatus": "not-enabled",
        "coverage": {"companyCount": len(reports),
                     "financialMetricCompanies": [r["ticker"] for r in reports if r["metrics"]],
                     "retainedDocumentCompanies": [r["ticker"] for r in reports if r.get("reportEvidence")]},
        "notice": "Deterministic review-only research. Curated IREN FY2026 baseline is not fresh collection. No AI run, auto-approval, price-target change or historical forecast surprise.",
    }


def main():
    observations = load(ROOT / "public/data/auto-financial-observations.json")
    iren = load(ROOT / "public/data/iren-fy26-source.json")
    inventory = load(ROOT / "public/data/official-sources.json")
    coverage = build_coverage(load(ROOT / "public/data/official-registry.json"),
                              load(ROOT / "public/data/report-intake.json"))
    data = build(observations, iren, inventory, coverage)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUT)
    print(json.dumps({"companies": len(data["reports"]),
                      "withMetrics": [r["ticker"] for r in data["reports"] if r["metrics"]],
                      "ai": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
