"""Strict, reproducible numeric extraction from *already downloaded* issuer table rows.

Pilot scope: dLocal Q2 2026 3-month release, sourced exclusively from the
scheduled official report collector. This adapter never hardcodes financial
results or approves an accounting observation.
"""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from report_intake import safe_report_url
from report_review_queue import version_id

VERSION = 1
MONEY = re.compile(r"^\(?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\)?$|^\(?[0-9]+(?:\.[0-9]+)?\)?$")
QUARTER = re.compile(r"^Three months ended on (March 31|June 30|September 30|December 31)$")
END_DATES = {"March 31": ("03-31", "01-01"), "June 30": ("06-30", "04-01"),
             "September 30": ("09-30", "07-01"), "December 31": ("12-31", "10-01")}

# The configuration identifies reviewed semantics, never an expected value.
PILOT = {
    "companyId": "us-dlo-nasdaq-a",
    "reportTitle": "dLocal Reports Second Quarter 2026 Financial Results",
    "reportPath": "/news-release/2026/08/13/3344936/0/en/dlocal-reports-second-quarter-2026-financial-results.html",
    "year": "2026",
    "quarterEnd": "June 30",
    "rules": (
        ("revenue", "Revenue", "Key Performance metrics", "In millions of US$", "IFRS (rounded issuer KPI)", 1.0),
        ("grossProfit", "Gross Profit", "Key Performance metrics", "In millions of US$", "IFRS (rounded issuer KPI)", 1.0),
        ("operatingCash", "Net cash (used in ) / generated from operating activities", "Adjusted Free Cash Flow reconciliation", "$ in thousands (except percentages)", "IFRS cash from operations as cited in reconciliation", 0.001),
        ("capex", "Capital expenditures²", "Adjusted Free Cash Flow reconciliation", "$ in thousands (except percentages)", "Issuer-defined cash capital expenditures (PPE plus intangibles)", 0.001),
    ),
}


def amount(raw):
    if not isinstance(raw, str) or not MONEY.fullmatch(raw):
        raise ValueError("Invalid source numeric cell")
    negative = raw.startswith("(") and raw.endswith(")")
    value = float(raw.strip("()").replace(",", ""))
    return -value if negative else value


def eligible(doc, company):
    if not isinstance(doc, dict) or doc.get("companyId") != PILOT["companyId"] or doc.get("title") != PILOT["reportTitle"]:
        return False
    url = doc.get("url")
    if not isinstance(url, str) or urlsplit(url).path != PILOT["reportPath"] or not safe_report_url(url, company):
        return False
    if doc.get("status") != "extracted" or doc.get("format") != "html":
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", str(doc.get("sha256", ""))):
        return False
    return isinstance(doc.get("tables"), list)


def period(t):
    rows = t.get("rows", [])
    if not isinstance(rows, list) or len(rows) < 3:
        raise ValueError("Missing source period headers")
    first, second = rows[:2]
    if not isinstance(first, list) or not isinstance(second, list) or len(first) < 2 or len(second) < 2:
        raise ValueError("Malformed source period headers")
    matched = QUARTER.fullmatch(str(first[1]).strip())
    if not matched or str(second[1]).strip() != PILOT["year"]:
        raise ValueError("Source is not the reviewed three-month FY2026 column")
    month_day = matched[1]
    if month_day != PILOT["quarterEnd"]:
        raise ValueError("Source quarter is not the reviewed pilot quarter")
    end, start = END_DATES[month_day]
    year = PILOT["year"]
    return year + "-" + start, year + "-" + end


def source_table(doc, heading, unit):
    matches = []
    for t in doc.get("tables", []):
        rows = t.get("rows") if isinstance(t, dict) else None
        if not isinstance(rows, list) or not rows:
            continue
        first = rows[0]
        if not isinstance(first, list) or not first:
            continue
        if heading == "Key Performance metrics":
            has_heading = any(isinstance(row, list) and row and row[0] == heading and len(row) >= 2 and unit in str(row[1]) for row in rows[:4])
        else:
            has_heading = unit in str(first[0]) and any(isinstance(row, list) and row and "Adjusted Free Cash Flow" == row[0] for row in rows)
        if has_heading:
            matches.append(t)
    if len(matches) != 1:
        raise ValueError("Source statement not uniquely identified")
    return matches[0]


def extract(intake, registry, previous=None):
    """Returns structured proposals, never approved observations."""
    previous = previous or {}
    company = next((c for c in registry.get("companies", []) if c.get("id") == PILOT["companyId"]), None)
    if not company:
        raise ValueError("Pilot company missing from registry")
    prior_entries = {e["id"]: e for e in previous.get("observations", []) if isinstance(e, dict) and isinstance(e.get("id"), str)}
    # This public data-branch artifact is only a candidate observation store.
    # An injected "approved" decision is NOT analyst authorization. Fail
    # closed rather than propagating it into future public snapshots.
    if any(e.get("reviewStatus") not in ("pending-review", "needs-reconciliation")
           for e in prior_entries.values()):
        raise ValueError("Untrusted approval state in persisted financial observations")
    entries = dict(prior_entries)
    issues = []
    detected = 0
    for doc in intake.get("documents", []):
        if not eligible(doc, company):
            continue
        # Every numeric observation must be associated with a content SHA
        # from the real collector, not from a manually typed source summary.
        review_id = version_id(doc["companyId"], doc["id"], doc["sha256"])
        # Never rely solely on the collector's mutable "revised" hint:
        # a changed source digest is a new review obligation even when the
        # issuer URL and report identity stay the same.
        prior_digest_changed = any(
            e.get("companyId") == doc["companyId"] and
            e.get("reportId") == doc["id"] and
            e.get("sourceSha256") != doc["sha256"]
            for e in prior_entries.values()
        )
        for key, label, heading, unit, basis, multiplier in PILOT["rules"]:
            try:
                t = source_table(doc, heading, unit)
                start, end = period(t)
                matches = [r[1] for r in t["rows"] if isinstance(r, list) and len(r) > 1 and r[0] == label]
                if len(matches) != 1:
                    raise ValueError("Source row missing or ambiguous")
                raw = matches[0]
                numeric = amount(raw)
                # CAPEX represents an expense magnitude, while the cash outflow
                # remains signed in source data.
                value = abs(numeric) * multiplier if key == "capex" and numeric <= 0 else numeric * multiplier
                if key == "capex" and numeric > 0:
                    raise ValueError("Investing cash outflow sign conflict")
                if not (abs(value) < 1e15):
                    raise ValueError("Non-finite source value")
                identifier = "observation:" + hashlib.sha256((review_id+"|"+key+"|"+start+"|"+end).encode()).hexdigest()[:32]
                existing = entries.get(identifier)
                revised_source = bool(doc.get("revised") or prior_digest_changed or
                                      (existing and existing.get("revisedSource")))
                needs_reconciliation = bool(revised_source or
                                            (existing and existing.get("reviewStatus") == "needs-reconciliation"))
                entries[identifier] = {
                    "id": identifier, "reviewVersionId": review_id, "companyId": doc["companyId"],
                    "reportId": doc["id"], "sourceUrl": doc["url"], "sourceSha256": doc["sha256"],
                    "sourceRow": label, "sourceTable": heading, "sourceRaw": raw,
                    "metricId": key, "value": round(value, 6), "unit": "USD million",
                    "sourceUnit": "USD million" if multiplier == 1 else "USD thousands",
                    "periodStart": start, "periodEnd": end, "period": "2026-Q2",
                    "periodKind": "three-month quarter", "basis": basis,
                    "publishedDate": doc.get("publishedDate"),
                    "collectedAt": doc.get("lastSuccessfulAt"),
                    "revisedSource": revised_source,
                    "reviewStatus": "needs-reconciliation" if needs_reconciliation else "pending-review",
                    "originalObservedAt": existing.get("originalObservedAt", doc.get("lastSuccessfulAt")) if existing else doc.get("lastSuccessfulAt"),
                    "note": "Automatically parsed candidate from issuer collector; pending accounting and period review.",
                }
                if existing is None:
                    detected += 1
            except (ValueError, KeyError, TypeError) as exc:
                issues.append({"companyId": doc["companyId"], "reportId": doc.get("id"), "metricId": key, "status": "needs-reconciliation", "reason": str(exc)})
    return {"version": VERSION, "generatedAt": intake.get("generatedAt"),
            "source": "public/data/report-intake.json", "observations": sorted(entries.values(), key=lambda e:e["id"]),
            "issues": issues, "newProposals": detected,
            "notice": "Proposed financial data from officially collected document rows only. Never auto-approved or applied to company valuations."}


def main():
    base = Path("public/data")
    intake = json.loads((base/"report-intake.json").read_text())
    registry = json.loads((base/"official-registry.json").read_text())
    path = base/"auto-financial-observations.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    result = extract(intake, registry, old)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    tmp.replace(path)
    print(json.dumps({"proposals":len(result["observations"]), "new":result["newProposals"], "issues":result["issues"]}))


if __name__ == "__main__":
    main()
