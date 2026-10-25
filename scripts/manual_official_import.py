"""Stage an independently downloaded *original* official issuer report.

This command NEVER fetches the Internet and NEVER publishes automatically.
A reviewer downloads the PDF from the issuer / SEC / official exchange,
checks issuer identity and the filing date, then stages the real file and
structured extraction (not just a curated JSON summary) outside public/data.

Manual stage JSON can be explicitly copied into public/data/report-intake.json
only after a human reviewed provenance, license, periods and financial rows.
The regular PULSE collect/compare/persist pipeline then takes over.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
from report_intake import MAX_BYTES, PARSER, extract, safe_report_url, valid_day
from official_sources import canonical

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "public/data/official-registry.json"
INTAKE = ROOT / "public/data/report-intake.json"


def stage(source, issuer, url, period, published, output_dir, *,
          registry=None, previous=None, reader=extract):
    """Return a candidate copy of the real intake feed, never change public data."""
    registry = registry or json.loads(REGISTRY.read_text(encoding="utf-8"))
    previous = previous if previous is not None else json.loads(INTAKE.read_text(encoding="utf-8"))
    companies = [c for c in registry.get("companies", []) if c.get("id") == issuer]
    if len(companies) != 1:
        raise ValueError("Issuer must match exactly one registered company")
    company = companies[0]
    if not safe_report_url(url, company):
        raise ValueError("Source URL not an official issuer-allowlisted report document")
    if not source.is_file() or source.is_symlink() or source.suffix.lower() != ".pdf":
        raise ValueError("Must provide a real regular PDF file")
    if not (source.stat().st_size > 100 and source.stat().st_size <= MAX_BYTES):
        raise ValueError("Original issuer PDF must be between 100 bytes and 8MB")
    if published and not valid_day(published):
        raise ValueError("Invalid issuer publication date")
    if not period or len(period) > 90:
        raise ValueError("Explicit issuer fiscal period is required")
    if not output_dir.is_absolute() or not output_dir.exists() or not output_dir.is_dir():
        raise ValueError("Staging directory must be an existing absolute private directory")
    if output_dir == ROOT or ROOT in output_dir.parents:
        # Never mix unscreened PDFs/identity materials into a public repository.
        raise ValueError("Private staging must be outside the public repository")
    if not isinstance(previous.get("documents"), list) or not isinstance(previous.get("sources"), list):
        raise ValueError("Previously accepted issuer intake is invalid")
    body = source.read_bytes()
    if not body.startswith(b"%PDF"):
        raise ValueError("Original document is not a PDF")
    digest = hashlib.sha256(body).hexdigest()
    result = reader(body, "application/pdf", url, company)
    if not isinstance(result, dict) or result.get("sha256") != digest:
        raise ValueError("Extractor digest mismatches original PDF bytes")
    if result.get("status") != "extracted" or not result.get("tables"):
        raise ValueError("Official PDF requires readable statement tables; manual import is not enough")
    if result.get("reviewStatus") != "pending-review" or result.get("format") != "pdf":
        raise ValueError("Unsafe manual observation status")
    result = dict(result)
    result.pop("links", None)
    moment = dt.datetime.now(dt.timezone.utc).isoformat()
    identity = "report:" + hashlib.sha256((issuer + "|" + canonical(url)).encode()).hexdigest()[:32]
    existing = next((d for d in previous["documents"] if d.get("id") == identity), None)
    record = dict(**result, id=identity, companyId=issuer, ticker=company["label"],
        url=url, finalUrl=url, publishedDate=published, documentPeriod=period,
        periodBasis="manual-original-file-fiscal-period-pending-verification",
        firstDetectedAt=existing.get("firstDetectedAt", moment) if existing else moment,
        lastSuccessfulAt=moment, lastAttemptAt=moment,
        revised=bool(existing and existing.get("sha256") != digest),
        revisions=((([{"sha256": existing["sha256"], "firstDetectedAt": existing.get("firstDetectedAt"),
                     "lastSuccessfulAt": existing.get("lastSuccessfulAt")}] +
                    existing.get("revisions", []))[:3]) if existing and existing.get("sha256") != digest
                   else existing.get("revisions", []) if existing else []),
        parserVersion=PARSER, error=None,
        provenance="manually-downloaded-original-pdf-human-verification-required")
    docs = [d for d in previous["documents"] if d.get("id") != identity] + [record]
    feed = dict(previous, generatedAt=moment, documents=docs)
    sources = [s for s in previous["sources"] if s.get("companyId") != issuer]
    sources.append({"companyId": issuer, "lastAttemptAt": moment, "status": "deferred",
                    "error": "Locally supplied official original; no new automated download",
                    "provenance": "local-original-upload-not-live-http-fetch"})
    feed["sources"] = sources
    feed["notice"] = (
        "Private staged issuer-source import; original PDF was supplied locally, not downloaded "
        "by GitHub Actions. Only publish after manual issuer identity and original period review.")
    # Exclusive create: never overwrite or follow arbitrary output symlinks.
    pdf_path = output_dir / ("issuer-" + issuer + "-" + digest + ".pdf")
    json_path = output_dir / ("issuer-" + issuer + "-" + digest + "-intake.json")
    if pdf_path.exists() or json_path.exists() or pdf_path.is_symlink() or json_path.is_symlink():
        raise ValueError("Cannot overwrite staged original issuer report")
    manifest = output_dir / ("issuer-" + issuer + "-" + digest + "-provenance.json")
    if manifest.exists() or manifest.is_symlink():
        raise ValueError("Cannot overwrite prior source-provenance file")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = []
    try:
        for path, content in [
            (pdf_path, body),
            (json_path, (json.dumps(feed, ensure_ascii=False, indent=2) + "\n").encode()),
            (manifest, (json.dumps({"companyId": issuer, "sourceUrl": url,
                "documentPeriod": period, "publishedDate": published,
                "originalPdfSha256": digest, "originalPdfBytes": len(body),
                "importedAt": moment, "reviewStatus": "pending-review",
                "provenance": "manual-file-not-retrieved-by-automated-collector",
                "identityReviewRequired": True, "pdfArchivedPublicly": False,
                "issuerDisplayName": company["name"]},
                ensure_ascii=False, indent=2) + "\n").encode()),
        ]:
            fd = os.open(path, flags, 0o600)
            created.append(path)
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return {"issuer": issuer, "sha256": digest, "pdf": str(pdf_path),
            "stagedFeed": str(json_path), "manifest": str(manifest),
            "numberOfTables": len(result["tables"]), "status": "human-review-required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--original-pdf", type=Path, required=True)
    parser.add_argument("--report-period", required=True)
    parser.add_argument("--published-date", default=None)
    parser.add_argument("--private-staging", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.original_pdf, args.issuer, args.source_url,
          args.report_period, args.published_date, args.private_staging),
          ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
