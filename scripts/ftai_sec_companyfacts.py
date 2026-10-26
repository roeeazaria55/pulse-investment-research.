"""Official SEC Company Facts fallback for FTAI 2026 Q2, fail-closed.

SEC XBRL facts are issuer assertions, not an approved valuation. Do not
infer quarter cash flows from six-month YTD totals. The issuer CIK, accession,
GAAP tag, exact comparative dates and numeric unit are always checked.
"""
import hashlib
import json
import math
from datetime import date

SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001590364.json"
FTAI_CIK = 1590364
Q2_ACCESSION = "0001628280-26-051412"
CURRENT = ("2026-04-01", "2026-06-30")
PRIOR = ("2025-04-01", "2025-06-30")
TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "OperatingIncomeLoss",
    "NetIncomeLoss",
)
ALIASES = ("FTAI AVIATION LTD", "FTAI AVIATION LTD.")


def read_ftai_companyfacts(body, url, company):
    """Return one safe FTAI retained original-JSON digest + same-accession facts.

    Only issuer's 2026 Q2 10-Q accession and exactly aligned comparative
    quarterly periods are accepted. No human-written text can become a fact.
    """
    if company.get("id") != "candidate-ftai" or url != SEC_URL:
        raise ValueError("SEC companyfacts URL or issuer not authorized")
    if len(body) > 8 * 1024 * 1024:
        raise ValueError("SEC companyfacts response exceeds 8MB")
    try:
        doc = json.loads(body)
    except (UnicodeError, ValueError) as e:
        raise ValueError("SEC companyfacts is not valid JSON") from e
    if not isinstance(doc, dict) or doc.get("cik") != FTAI_CIK or not isinstance(doc.get("entityName"), str) or doc["entityName"].strip().upper() not in ALIASES:
        raise ValueError("SEC companyfacts issuer CIK/name mismatch")
    gaap = doc.get("facts", {}).get("us-gaap", {})
    if not isinstance(gaap, dict):
        raise ValueError("SEC companyfacts missing US GAAP facts")
    extracted = []
    for name in TAGS:
        data = gaap.get(name)
        if not isinstance(data, dict):
            continue
        usd = data.get("units", {}).get("USD", [])
        if not isinstance(usd, list):
            continue
        matched = {}
        for row in usd:
            if not isinstance(row, dict):
                continue
            if (row.get("accn") != Q2_ACCESSION or row.get("form") != "10-Q" or
                (row.get("start"), row.get("end")) not in (CURRENT, PRIOR) or
                not isinstance(row.get("filed"), str)):
                continue
            try:
                filed = date.fromisoformat(row["filed"])
            except ValueError:
                continue
            if filed.isoformat() != "2026-07-31":
                continue
            val = row.get("val")
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or abs(val) > 1e15:
                continue
            key = (row["start"], row["end"])
            if key in matched and matched[key] != val:
                matched[key] = None  # Ambiguous same fiscal period.
            elif key not in matched:
                matched[key] = val
        # A quarter comparison must be derived from the same official
        # filing, not another accession, frame, FY or H1 context.
        if len(matched) != 2 or any(matched.get(k) is None for k in (CURRENT, PRIOR)):
            continue
        for (start, end) in (CURRENT, PRIOR):
            extracted.append({
                "concept": "us-gaap:" + name.lower(),
                "value": matched[(start, end)],
                "unit": "iso4217:USD", "start": start, "end": end,
                "context": "SEC-CompanyFacts:" + Q2_ACCESSION,
                "status": "structured-source",
                "definition": "Official SEC Company Facts: " + name +
                              " 2026-07-31 accession, unaudited Q2 duration",
            })
    if not extracted:
        raise ValueError("No uniquely comparable FTAI SEC Q2 issuer facts")
    return {
        "status": "extracted",
        "title": "FTAI AVIATION LTD. 2026 Q2 10-Q SEC Company Facts (CIK 1590364)",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body), "format": "sec-json", "pages": None,
        "readScope": "selected-Q2-2026-SEC-accession-facts",
        "charactersRead": len(body), "tables": [], "tableCount": 0,
        "tablesTruncated": False, "facts": extracted, "sourcePdfPages": [],
        "reviewStatus": "pending-review", "links": [],
        "secAccession": Q2_ACCESSION, "cik": FTAI_CIK,
        "notice": "SHA-256 of original downloaded SEC Company Facts JSON bytes; "
                  "only SEC GAAP Q2 2026/2025 facts extracted, not a retained original binary archive.",
    }
