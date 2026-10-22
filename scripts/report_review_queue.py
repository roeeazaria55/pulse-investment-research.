"""Turn real report-intake snapshots into a durable, review-only version queue.

This module never maps an unreviewed source row to an investment metric and
never edits company models. The queue is an audit aid, not a valuation signal.
"""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from report_intake import safe_report_url

VERSION = 1
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_ENTRIES = 180


def valid_time(value):
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def valid_document(doc, companies):
    if not isinstance(doc, dict):
        return False
    if doc.get("companyId") not in companies or not isinstance(doc.get("id"), str):
        return False
    if not doc["id"].startswith("report:") or not HEX_SHA.fullmatch(str(doc.get("sha256", ""))):
        return False
    if doc.get("status") not in ("extracted", "read-no-supported-data"):
        return False
    u = urlsplit(str(doc.get("url", "")))
    if u.scheme != "https" or not u.hostname or u.username or u.password or not safe_report_url(doc["url"], companies[doc["companyId"]]):
        return False
    if not valid_time(doc.get("lastSuccessfulAt")):
        return False
    return True


def version_id(company_id, report_id, sha):
    return "review:" + hashlib.sha256((company_id + "|" + report_id + "|" + sha).encode()).hexdigest()[:32]


def build_queue(intake, registry, previous, now):
    """Stable report+content version identities. No automatic review approval."""
    if not valid_time(now) or intake.get("version") != 1 or not isinstance(intake.get("documents"), list):
        raise ValueError("Invalid report-intake snapshot")
    if not isinstance(registry.get("companies"), list):
        raise ValueError("Invalid issuer registry")
    companies = {c["id"]: c for c in registry["companies"] if isinstance(c, dict) and c.get("id")}
    past = {e["id"]: e for e in previous.get("entries", []) if isinstance(e, dict) and isinstance(e.get("id"), str)}
    entries = {k: v for k, v in past.items() if v.get("companyId") in companies and v.get("reviewStatus") == "pending-review"}
    present_keys = set()
    accepted, rejected = 0, 0
    new_versions, revised_versions = 0, 0
    for doc in intake["documents"]:
        if not valid_document(doc, companies):
            rejected += 1
            continue
        accepted += 1
        company_id, report_id, sha = doc["companyId"], doc["id"], doc["sha256"]
        ident = version_id(company_id, report_id, sha)
        present_keys.add(ident)
        old = entries.get(ident)
        previous_versions = [e for e in entries.values()
                             if e.get("reportId") == report_id and e.get("companyId") == company_id
                             and e.get("id") != ident]
        is_revision = bool(doc.get("revised") or previous_versions or doc.get("revisions"))
        if old is None:
            new_versions += 1
            if is_revision:
                revised_versions += 1
        tables = doc.get("tableCount", 0)
        facts = doc.get("facts", [])
        entries[ident] = {
            "id": ident,
            "companyId": company_id,
            "ticker": companies[company_id].get("ticker", doc.get("ticker", "")),
            "reportId": report_id,
            "sourceUrl": doc["url"],
            "sha256": sha,
            "firstObservedAt": old.get("firstObservedAt", now) if old else now,
            "lastSuccessfulAt": doc["lastSuccessfulAt"],
            "lastSeenAt": now,
            "publishedDate": doc.get("publishedDate") if isinstance(doc.get("publishedDate"), str) else None,
            "documentPeriod": doc.get("documentPeriod") if isinstance(doc.get("documentPeriod"), str) else None,
            "periodReview": "unverified-source-metadata",
            "parserVersion": doc.get("parserVersion"),
            "tableCount": tables if isinstance(tables, int) and tables >= 0 else 0,
            "structuredFactCount": len(facts) if isinstance(facts, list) else 0,
            "contentStatus": doc["status"],
            "refreshError": doc.get("error") if isinstance(doc.get("error"), str) else None,
            "revised": is_revision,
            "reviewStatus": "pending-review",
            "notice": "Source evidence only; accounting definitions, dates and units require analyst review.",
        }

    # Keep a bounded history of superseded versions, without pretending a
    # failed refresh (or removed source) is a fresh successful observation.
    newest_for_report = {}
    for key in present_keys:
        entry = entries[key]
        marker = (entry["companyId"], entry["reportId"])
        current = newest_for_report.get(marker)
        if current is None or (entry["lastSuccessfulAt"], key) > (current["lastSuccessfulAt"], current["id"]):
            newest_for_report[marker] = entry
    for entry in entries.values():
        marker = (entry["companyId"], entry["reportId"])
        entry["currentVersion"] = bool(entry["id"] in present_keys and newest_for_report.get(marker, {}).get("id") == entry["id"])
    items = sorted(entries.values(), key=lambda e: (e.get("lastSuccessfulAt") or "", e["id"]), reverse=True)[:MAX_ENTRIES]
    failures = []
    for source in intake.get("sources", []):
        if not isinstance(source, dict) or source.get("companyId") not in companies:
            continue
        if source.get("status") in ("failed", "partial", "deferred"):
            failures.append({"companyId": source["companyId"], "status": source["status"],
                             "error": source.get("error") if isinstance(source.get("error"), str) else None})
    return {
        "version": VERSION,
        "generatedAt": now,
        "sourceSnapshotAt": intake.get("generatedAt"),
        "entries": items,
        "failures": failures,
        "summary": {"sourceDocuments": accepted, "invalidDocuments": rejected,
                    "newPendingVersions": new_versions, "newRevisedVersions": revised_versions,
                    "pendingVersions": len(items), "failedOrDeferredSources": len(failures)},
        "notice": "Pending review queue only. No automatic financial mapping, valuation, price target or forecast update. A failed source does not mean no report was published.",
    }


def main():
    root = Path("public/data")
    intake = json.loads((root / "report-intake.json").read_text())
    registry = json.loads((root / "official-registry.json").read_text())
    path = root / "report-review-queue.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    queue = build_queue(intake, registry, old, now)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(json.dumps(queue["summary"]))


if __name__ == "__main__":
    main()
