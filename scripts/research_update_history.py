"""Immutable, public-only bounded history of source-backed PULSE research updates.

The last-seen timestamp is collection metadata; report publication dates remain
the authoritative date for financial recency. Never import user/portfolio data.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
LATEST = ROOT / "public/data/latest-research-updates.json"
OUTPUT = ROOT / "public/data/research-update-history.json"
MAX_PER_ISSUER = 12
ALLOWED = {c["id"] for c in json.loads((ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))["companies"]}
ID = re.compile(r"^[0-9a-f]{24}$")


def _time(value):
    if not isinstance(value, str):
        raise ValueError("Missing history timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Invalid history timestamp") from exc


def _entry(report, first_seen):
    if not isinstance(report, dict) or report.get("companyId") not in ALLOWED:
        raise ValueError("Unrecognized issuer in history")
    content_id = report.get("contentId")
    if not isinstance(content_id, str) or not ID.fullmatch(content_id):
        raise ValueError("Malformed research content ID")
    if not isinstance(report.get("metrics"), list) or not report["metrics"]:
        raise ValueError("History cannot promote empty or unverified report")
    if report.get("reviewRequired") is not True or report.get("aiAnalysisEnabled") is not False:
        raise ValueError("Non-review research cannot enter public history")
    if report.get("status") not in ("needs-reconciliation", "pending-review", "historical-baseline-pending-review"):
        raise ValueError("Unsafe source status")
    _time(first_seen)
    # Fetch-health timestamps and retained-document last-success metadata vary
    # on every run; they must never masquerade as a new research revision.
    # Historical evidence is sourced from the stable report URL/sha/metrics.
    volatile = {"reportEvidence", "intakeStatus", "intakeAttemptAt",
                "intakeSuccessAt", "intakeError", "issuerPortal", "analystQuestions"}
    stable_report = {k:v for k,v in report.items() if k not in volatile}
    return {
        "companyId": report["companyId"], "ticker": report["ticker"],
        "contentId": content_id, "firstSeenAt": first_seen,
        "reportPeriod": report.get("reportPeriod"),
        "publishedDate": report.get("publishedDate"),
        "sourceVersion": report.get("sourceVersion"),
        "status": report["status"], "report": stable_report,
    }


def combine(previous, latest):
    if not isinstance(latest, dict) or latest.get("version") != 1 or not isinstance(latest.get("reports"), list):
        raise ValueError("Invalid latest research feed")
    now = latest.get("generatedAt")
    _time(now)
    if previous is None:
        previous = {"version": 1, "updatedAt": now, "entries": []}
    if not isinstance(previous, dict) or previous.get("version") != 1 or not isinstance(previous.get("entries"), list):
        raise ValueError("Invalid saved research history")
    if len(previous["entries"]) > len(ALLOWED) * MAX_PER_ISSUER:
        raise ValueError("Unbounded saved research history")
    entries, known = [], set()
    for prior in previous["entries"]:
        if not isinstance(prior, dict):
            raise ValueError("Malformed saved history entry")
        rec = _entry(prior.get("report"), prior.get("firstSeenAt"))
        if any(prior.get(k) != rec[k] for k in rec):
            raise ValueError("History metadata disagrees with immutable report")
        key = (rec["companyId"], rec["contentId"])
        if key in known:
            raise ValueError("Duplicate immutable history ID")
        known.add(key)
        entries.append(rec)
    additions = 0
    for report in latest["reports"]:
        if report.get("companyId") not in ALLOWED:
            raise ValueError("Unrecognized current issuer")
        if not report.get("metrics"):
            continue
        rec = _entry(report, now)
        key = (rec["companyId"], rec["contentId"])
        if key not in known:
            entries.append(rec)
            known.add(key)
            additions += 1
        elif next(item for item in entries if (item["companyId"], item["contentId"]) == key)["report"] != report:
            raise ValueError("Research content changed without a version increment")
    result = []
    for company in sorted(ALLOWED):
        matching = [e for e in entries if e["companyId"] == company]
        matching.sort(key=lambda e: (_time(e["firstSeenAt"]), e["contentId"]), reverse=True)
        result.extend(matching[:MAX_PER_ISSUER])
    # Repeated collection is not a new research event and does not rewrite the file.
    result.sort(key=lambda e: (e["companyId"], e["firstSeenAt"], e["contentId"]))
    return {"version": 1, "updatedAt": now if additions else previous["updatedAt"],
            "entries": result}, additions


def main():
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.is_file() else None
    result, added = combine(previous, latest)
    if previous == result:
        print(json.dumps({"newVersions": 0, "retained": len(result["entries"]), "changed": False}))
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUTPUT)
    print(json.dumps({"newVersions": added, "retained": len(result["entries"]), "changed": True}))


if __name__ == "__main__":
    main()
