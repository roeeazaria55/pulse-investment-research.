"""Deterministic issuer document coverage + conservatively typed XBRL observations.

Works exclusively on already retained public issuer content. Discovery success
is NOT content success, and raw source facts are NOT analyst-approved. The
intent is to expose 12/12 honest company states, not fabricate quarterlies.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import json
import math
import re

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/data/issuer-coverage.json"
DIGEST = re.compile(r"^[a-f0-9]{64}$")
XBRL = {
    "us-gaap:revenuefromcontractwithcustomerexcludingassessedtax": ("revenue", "הכנסות", "US GAAP Revenue from Contracts"),
    "us-gaap:revenues": ("revenue", "הכנסות", "US GAAP Revenues"),
    "us-gaap:grossprofit": ("grossProfit", "רווח גולמי", "US GAAP Gross Profit"),
    "us-gaap:netcashprovidedbyusedinoperatingactivities": ("operatingCash", "תזרים תפעולי", "US GAAP Net Cash Provided by Operating Activities"),
}
MAX_METRICS = 4


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_official_url(url, company):
    if not isinstance(url, str) or len(url) > 2000:
        return False
    try:
        p = urlsplit(url)
        return p.scheme == "https" and p.hostname in company["allowedHosts"] and (
            not p.username and not p.password and p.port in (None, 443)
        ) and any(p.path.startswith(prefix) for prefix in company["documentPaths"])
    except ValueError:
        return False


def iso_date(s):
    if not isinstance(s, str):
        return False
    try:
        return date.fromisoformat(s).isoformat() == s
    except ValueError:
        return False


def document_usable(doc, company):
    return (isinstance(doc, dict) and doc.get("companyId") == company["id"]
        and doc.get("status") == "extracted"
        and isinstance(doc.get("sha256"), str) and bool(DIGEST.fullmatch(doc["sha256"]))
        and isinstance(doc.get("id"), str) and doc["id"].startswith("report:")
        and is_official_url(doc.get("url"), company)
        and doc.get("format") in ("html", "pdf")
        and (isinstance(doc.get("tables"), list) or isinstance(doc.get("facts"), list)))


def status_for(source_rows):
    if not source_rows:
        return "unconfigured"
    statuses = [s.get("status") for s in source_rows]
    if any(v not in ("ok", "failed", "partial", "no-candidates", "deferred") for v in statuses):
        raise ValueError("Unexpected document fetch status")
    if any(v in ("failed", "partial", "deferred") for v in statuses):
        return "partial" if any(v == "ok" for v in statuses) else "failed"
    if any(v == "ok" for v in statuses):
        return "ok"
    return "no-candidates"


def safe_source_facts(doc):
    """Only unambiguous, period-bound USD XBRL facts from stored SEC reports.

    HTML/PDF table layout alone is not sufficiently trustworthy for a generic
    numeric mapping. Duration facts must span 75..380 days and match full
    context lengths for the comparison; overlapping XBRL tags are never merged.
    """
    facts = doc.get("facts", [])
    if not isinstance(facts, list):
        return []
    grouped = {}
    for f in facts:
        if not isinstance(f, dict) or f.get("concept") not in XBRL or f.get("unit") != "iso4217:USD":
            continue
        start, end, value = f.get("start"), f.get("end"), f.get("value")
        if (not iso_date(start) or not iso_date(end)
            or isinstance(value, bool) or not isinstance(value, (float, int))
            or not math.isfinite(value)):
            continue
        duration = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
        if not 75 <= duration <= 380:
            continue
        key = XBRL[f["concept"]][0]
        grouped.setdefault(key, []).append((end, start, f["concept"], value, f.get("context")))
    proposals = []
    for metric_id, rows in grouped.items():
        latest_period = max(row[0] for row in rows)
        current = [r for r in rows if r[0] == latest_period]
        if len(current) != 1:
            # Different tags or repeated contexts could be consolidated vs segment.
            continue
        end, start, concept, value, context = current[0]
        length = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
        candidates = [r for r in rows if r[2] == concept and r[0] < end
                      and abs(((date.fromisoformat(r[0])-date.fromisoformat(r[1])).days+1)-length) <= 2]
        candidates.sort(key=lambda r: r[0], reverse=True)
        previous = candidates[0] if candidates and len([r for r in candidates if r[0] == candidates[0][0]]) == 1 else None
        # Never present a value comparison as a forecast beat/miss.
        prior = previous[3] if previous else None
        pct = round((value-prior)/abs(prior)*100, 2) if prior not in (None, 0) else None
        label = XBRL[concept][1]
        proposals.append({
            "id": metric_id, "label": label, "value": round(value/1e6, 6),
            "previousValue": round(prior/1e6, 6) if prior is not None else None,
            "changePercent": pct, "unit": "USD million",
            "periodStart": start, "periodEnd": end,
            "previousPeriodStart": previous[1] if previous else None,
            "previousPeriodEnd": previous[0] if previous else None,
            "accountingBasis": XBRL[concept][2] + " — structured XBRL (needs review)",
            "sourceRow": concept, "sourceRaw": str(value),
            "sourcePreviousRaw": str(prior) if prior is not None else None,
            "sourcePage": None, "sourceDocumentUrl": None, "sourceUrl": doc["url"],
            "reviewStatus": "pending-review",
            "comparison": ("Same tagged accounting definition and duration; candidate prior "
                           "period only, not a verified forecast surprise." if previous else
                           "No unique same-tag prior-duration candidate."),
            "evidenceScope": "retained-sec-inline-xbrl",
            "sourceSha256": doc["sha256"],
            "reportId": doc["id"],
            "sourceContext": context,
        })
    return sorted(proposals, key=lambda r: r["id"])[:MAX_METRICS]


def report_rank(doc):
    # Date/period from issuer metadata, never from time of download alone.
    period = doc.get("documentPeriod") or ""
    hint = re.search(r"(?:FY|Q[1-4]\s*)\s*(20\d\d)", period, re.I)
    return (doc.get("publishedDate") if iso_date(doc.get("publishedDate")) else "",
            hint.group(1) if hint else "", doc.get("lastSuccessfulAt") or "")


def build(registry, intake):
    companies = registry.get("companies")
    if not isinstance(companies, list) or len(companies) != 12:
        raise ValueError("Expected exactly 12 official PULSE companies")
    docs = intake.get("documents")
    statuses = intake.get("sources")
    if not isinstance(docs, list) or not isinstance(statuses, list):
        raise ValueError("Missing issuer intake evidence")
    covered = []
    ids = set()
    for c in companies:
        if not isinstance(c, dict) or c.get("id") in ids or not isinstance(c.get("allowedHosts"), list):
            raise ValueError("Duplicate or malformed company registry")
        ids.add(c["id"])
        company_docs = sorted((d for d in docs if document_usable(d, c)), key=report_rank, reverse=True)
        checks = [s for s in statuses if isinstance(s, dict) and s.get("companyId") == c["id"]]
        fetch_state = status_for(checks)
        latest = company_docs[0] if company_docs else None
        proposal = safe_source_facts(latest) if latest else []
        candidate = None
        if latest:
            candidate = {
                "id": latest["id"], "url": latest["url"], "sha256": latest["sha256"],
                "title": latest.get("title", "")[:240], "format": latest["format"],
                "publishedDate": latest.get("publishedDate") if iso_date(latest.get("publishedDate")) else None,
                "documentPeriod": latest.get("documentPeriod") or None,
                "firstDetectedAt": latest.get("firstDetectedAt"),
                "lastSuccessfulAt": latest.get("lastSuccessfulAt"),
                "reviewStatus": "pending-review", "sourceIsCurrentlyReachable": fetch_state == "ok",
                "note": "Latest retained eligible document by available metadata; not proof of latest issuer filing.",
            }
        covered.append({
            "companyId": c["id"], "ticker": c.get("label") or c.get("ticker") or c["name"],
            "intakeStatus": fetch_state, "intakeAttemptAt": max(
                (s.get("lastAttemptAt") for s in checks if isinstance(s.get("lastAttemptAt"), str)), default=None),
            "intakeSuccessAt": max(
                (s.get("lastSuccessfulAt") for s in checks if isinstance(s.get("lastSuccessfulAt"), str)), default=None),
            "lastError": next((s.get("error") for s in checks if s.get("error")), None),
            "retainedDocumentCount": len(company_docs),
            "report": candidate, "typedMetrics": proposal,
            "metricCoverage": ("provisional-xbrl" if proposal else "report-only" if candidate else "no-document"),
            "issuerPortal": next((s["url"] for s in c.get("sources", []) if
                                  isinstance(s, dict) and isinstance(s.get("url"), str)
                                  and s["url"].startswith("https://")), None),
            "analystQuestions": c.get("questions", [])[:3],
        })
    return {"version": 1, "coverage": covered,
            "notice": "12/12 indexed. Report links are retained evidence, not currently verified downloads. "
                      "Only uniquely scoped, structured USD XBRL values are financial proposals."}


def main():
    result = build(read(ROOT / "public/data/official-registry.json"),
                   read(ROOT / "public/data/report-intake.json"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"companies": len(result["coverage"]),
                      "retainedDocs": [r["ticker"] for r in result["coverage"] if r["report"]],
                      "financialCandidates": [r["ticker"] for r in result["coverage"] if r["typedMetrics"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
