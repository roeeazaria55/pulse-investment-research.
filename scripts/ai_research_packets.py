"""Build auditable, read-only AI research input packets from PULSE source files.

No model/API invocation, valuations, portfolio holdings or external network calls.
Files and scraped content are untrusted DATA, never operational instructions.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import ipaddress
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
# Every registered issuer has a stable ASCII output key. TASE companies use
# the exact registry company ID where there is no exchange ticker.
TICKERS = tuple(
    c.get("ticker") or c["id"]
    for c in json.loads((ROOT / "public/data/official-registry.json").read_text(encoding="utf-8"))["companies"]
)
FIELDS = ("thesis", "revenue", "profitability", "cashFlow", "valuation",
          "advantages", "catalysts", "risks", "bear", "base", "bull")
SHA = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,50}$")

def read_json(path: Path, *, optional=False):
    if not path.is_file():
        if optional:
            return None
        raise ValueError("Required source unavailable: " + str(path.relative_to(ROOT)))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid source JSON: " + str(path)) from exc

def source_ref(path: Path):
    content = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(content).hexdigest()}

def _issuer_host_allowed(host, company):
    """Only an explicit list of exact hostnames grants issuer-source authority."""
    allowed = company.get("allowedHosts")
    return (isinstance(allowed, list) and bool(allowed)
            and all(isinstance(item, str) and item for item in allowed)
            and host in allowed)


def _https_issuer_host_url(raw, company):
    """Common HTTPS/host gate; portal links need not be document URLs."""
    if (not isinstance(raw, str) or not raw or len(raw) > 2048
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw)
            or "\\" in raw):
        return None
    try:
        u = urlsplit(raw)
        host = (u.hostname or "").lower()
        if not _issuer_host_allowed(host, company):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        if (u.scheme != "https" or u.username or u.password
                or u.port not in (None, 443) or u.fragment):
            return None
        return u
    except (ValueError, TypeError, AttributeError):
        return None


def https_issuer_url(raw, company):
    u = _https_issuer_host_url(raw, company)
    paths = company.get("documentPaths")
    return (u is not None and isinstance(paths, list) and bool(paths)
            and all(isinstance(path, str) and path.startswith("/")
                    and path != "/" for path in paths)
            and bool(u.path) and u.path.startswith(tuple(paths)))


def official_portal_sources(company):
    """Treat registry portal URLs as unverified links, never issuer facts."""
    raw = company.get("sources")
    if not isinstance(raw, list) or len(raw) > 30:
        raise ValueError("Invalid issuer portal registry")
    seen = set()
    result = []
    for source in raw:
        if not isinstance(source, dict):
            raise ValueError("Malformed issuer portal entry")
        sid, label, url = source.get("id"), source.get("label"), source.get("url")
        if (not isinstance(sid, str) or not ID.fullmatch(sid) or sid in seen
                or not text(label, 200)
                or "\\" in label
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in label)
                or _https_issuer_host_url(url, company) is None):
            raise ValueError("Untrusted issuer portal metadata")
        seen.add(sid)
        result.append({"label": label, "url": url,
                       "reviewStatus": "registry-link-not-an-observation"})
    return result

def text(value, max_length=12000):
    return isinstance(value, str) and 0 < len(value) <= max_length

def research_questions(company):
    """Preserve issuer-registry prompts as untrusted data; never silently drop any.

    These questions are research topics, not trusted analyst instructions.
    Missing, malformed or excess entries are evidence-integrity errors.
    """
    questions = company.get("questions")
    if not isinstance(questions, list) or not 1 <= len(questions) <= 20:
        raise ValueError("Malformed issuer research questions")
    seen = set()
    for question in questions:
        if (not text(question, 1000) or not question.strip()
                or "\\" in question
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in question)
                or question in seen):
            raise ValueError("Malformed issuer research question")
        seen.add(question)
    return list(questions)


def safe_period(value):
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False

def numeric(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)

def required_object_rows(source, key, description):
    """Fail closed when a required evidence collection has been corrupted.

    A missing list or a string/dict substituted for it must not silently
    become an empty packet that claims no evidence was available.
    """
    if not isinstance(source, dict):
        raise ValueError("Malformed " + description)
    rows = source.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Malformed " + description)
    return rows


def financial_observations(company, observations, source_ref_name):
    result = []
    seen = set()
    for row in observations:
        if not isinstance(row, dict) or row.get("companyId") != company["id"]:
            continue
        required = ("id", "reportId", "reviewVersionId", "sourceUrl", "sourceSha256",
                    "metricId", "sourceRow", "sourceRaw", "sourceUnit", "unit",
                    "basis", "periodStart", "periodEnd", "periodKind", "reviewStatus")
        if any(not text(row.get(k), 900) for k in required):
            raise ValueError("Unusable accounting evidence: missing fields")
        if (not https_issuer_url(row["sourceUrl"], company)
            or not SHA.fullmatch(row["sourceSha256"])
            or not safe_period(row["periodStart"])
            or not safe_period(row["periodEnd"])
            or row["periodStart"] > row["periodEnd"]
            or not numeric(row.get("value"))
            or row["reviewStatus"] not in ("pending-review", "needs-reconciliation")):
            raise ValueError("Untrusted, invalid or overpromoted accounting observation")
        if row["id"] in seen:
            raise ValueError("Duplicate financial observation")
        seen.add(row["id"])
        result.append({
            "observationId": row["id"], "reportId": row["reportId"],
            "reviewVersionId": row["reviewVersionId"], "sourceSha256": row["sourceSha256"],
            "sourceUrl": row["sourceUrl"], "sourceRow": row["sourceRow"],
            "rawValue": row["sourceRaw"], "sourceUnit": row["sourceUnit"],
            "normalizedValue": row["value"], "unit": row["unit"],
            "metricId": row["metricId"], "accountingBasis": row["basis"],
            "periodStart": row["periodStart"], "periodEnd": row["periodEnd"],
            "periodKind": row["periodKind"], "publishedDate": row.get("publishedDate"),
            "reviewStatus": row["reviewStatus"], "revisedSource": bool(row.get("revisedSource")),
            "verification": "needs-reconciliation" if row["reviewStatus"] == "needs-reconciliation"
                            else "pending-review", "modelEligible": False,
            "provenanceFile": source_ref_name,
        })
    return sorted(result, key=lambda x: x["observationId"])

def forecast_history(company, archive):
    """Preserve every matching forecast or reject the source; never hide bad rows.

    Archive timestamps and commit hashes are *syntax checked*, not authenticated.
    No archived forecast becomes an approved historical backtest or issuer fact.
    """
    rows = []
    seen = set()
    expected_ticker = provenance_ticker(company)
    for f in archive:
        if not isinstance(f, dict):
            raise ValueError("Malformed archived forecast record")
        if f.get("companyId") != company["id"]:
            if expected_ticker and f.get("ticker") == expected_ticker:
                raise ValueError("Archived forecast issuer identity mismatch")
            continue
        point = f.get("point")
        required = ("id", "metricId", "ticker", "firstRecordedAt",
                    "firstRecordedCommit", "researchAsOf", "chronologyStatus")
        if (f.get("ticker") != expected_ticker
            or any(not text(f.get(key), 900) for key in required)
            or not re.fullmatch(r"forecast:[0-9a-f]{32}", f["id"])
            or not re.fullmatch(r"[0-9a-f]{40}", f["firstRecordedCommit"])
            or not safe_period(f["researchAsOf"])
            or not isinstance(point, dict)
            or not numeric(point.get("value"))
            or any(not text(point.get(key), 900) for key in ("unit", "basis", "period"))
            or f.get("canBeUsedForHistoricalBacktest") is not False):
            raise ValueError("Invalid archived forecast evidence for " + company["ticker"])
        try:
            recorded_at = dt.datetime.fromisoformat(
                f["firstRecordedAt"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid archived forecast firstRecordedAt") from exc
        if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
            raise ValueError("Archived forecast timestamp must have timezone")
        if f["id"] in seen:
            raise ValueError("Duplicate archived forecast identifier")
        seen.add(f["id"])
        rows.append({
            "id": f["id"], "metricId": f["metricId"],
            "point": {key: point[key] for key in ("value", "unit", "basis", "period")},
            "firstRecordedAt": f["firstRecordedAt"],
            "firstRecordedCommit": f["firstRecordedCommit"],
            "claimedResearchDate": f["researchAsOf"],
            "chronologyStatus": "research-asof-unverified",
            "historicalBacktestVerified": False,
            "role": "archived-analyst-forecast",
        })
    return sorted(rows, key=lambda x: x["id"])

# A comparison is a derived, unverified claim, not approval or a backtest.
# These are the fixed reasons emitted by forecast_actual_comparison.compare().
BLOCKED_REASONS = frozenset((
    "company mismatch",
    "metric mismatch",
    "period mismatch: no annualization or YTD substitution",
    "unit mismatch: no unreviewed conversion",
    "accounting-definition mismatch",
    "forecast was not demonstrably archived before result publication",
    "observation is not approved by a merged analyst review",
    "Review Decision Recorded; analyst approval is not verified by an enforced repository policy",
    "invalid numeric value",
))


def validate_comparison_evidence(rows, observations, forecasts):
    """Reject forged comparison authority and orphan/duplicate evidence links.

    Even a well-formed blocked result is only an unverified derived claim.
    The source file and its hash must be carried in the research packet.
    """
    actual_by_id = {}
    forecast_by_id = {}
    for source_rows, target, name in (
        (observations, actual_by_id, "observation"),
        (forecasts, forecast_by_id, "forecast"),
    ):
        for item in source_rows:
            identifier = item.get("id")
            if not text(identifier, 150) or identifier in target:
                raise ValueError("Ambiguous comparison " + name + " identity")
            target[identifier] = item
    seen = set()
    for row in rows:
        actual_id, forecast_id = row.get("observationId"), row.get("forecastId")
        pair = (forecast_id, actual_id)
        reasons = row.get("reasons")
        if (not isinstance(actual_id, str) or not isinstance(forecast_id, str)
            or actual_id not in actual_by_id or forecast_id not in forecast_by_id
            or pair in seen
            or row.get("status") != "blocked"
            or row.get("difference", "missing") is not None
            or row.get("percent", "missing") is not None
            or not isinstance(reasons, list) or not reasons or len(reasons) > len(BLOCKED_REASONS)
            or any(not isinstance(reason, str) or reason not in BLOCKED_REASONS
                   for reason in reasons)
            or len(set(reasons)) != len(reasons)):
            raise ValueError("Invalid or overpromoted comparison evidence")
        actual, forecast = actual_by_id[actual_id], forecast_by_id[forecast_id]
        if (actual.get("companyId") != forecast.get("companyId")
            or actual.get("metricId") != forecast.get("metricId")):
            raise ValueError("Cross-issuer or cross-metric comparison identity")
        seen.add(pair)


def research_for(company, sources):
    ticker = company["ticker"].lower()
    path = ROOT / "src/data/research" / (ticker + ".json")
    if not path.exists() and ticker == "nbis":
        path = ROOT / "src/data/nbis-research.json"
    if not path.exists():
        return None
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Malformed analyst research document")
    record = raw.get("analysis", raw)
    if not isinstance(record, dict):
        raise ValueError("Malformed analyst research record")
    if record.get("companyId") != company["id"]:
        raise ValueError("Cross-company research mismatch")
    # A missing, falsey or wrong-shaped collection must not silently erase
    # analyst caveats or source narratives from an AI input packet.
    fields = record.get("fields")
    if not isinstance(fields, dict) or not any(key in fields for key in FIELDS):
        raise ValueError("Malformed analyst research sections")
    missing = record.get("missing", [])
    if (not isinstance(missing, list) or len(missing) > 30
            or any(not text(item, 1200) for item in missing)):
        raise ValueError("Malformed analyst research limitations")
    as_of = record.get("asOf")
    if as_of is not None and not safe_period(as_of):
        raise ValueError("Malformed analyst research date claim")
    scope = raw.get("scope")
    if scope is not None and not text(scope, 500):
        raise ValueError("Malformed analyst research scope")
    excerpts = {}
    for key in FIELDS:
        if key in fields:
            if not text(fields[key]):
                raise ValueError("Malformed analyst research section: " + key)
            excerpts[key] = {"rawResearchText": fields[key],
                             "classification": "unverified-analyst-narrative",
                             "untrustedInstructions": True}
    sources.append(source_ref(path))
    return {"researchAsOfClaim": as_of, "reviewStatus": "analyst-research-unverified",
            "sections": excerpts, "sourceFile": sources[-1], "scope": scope,
            "limitations": list(missing)}

def validated_model_scenarios(raw, company):
    """Reject malformed model assumptions instead of exporting partial scenarios.

    This is structural validation of existing analyst hypotheses, not approval
    of the assumptions or a recalculation of targets/probabilities.
    """
    if (not isinstance(raw, dict) or raw.get("version") != 1
            or raw.get("companyId") != company["id"]
            or raw.get("ticker") != company["ticker"]):
        raise ValueError("Malformed or cross-issuer valuation model identity")
    scenarios = raw.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 3:
        raise ValueError("Malformed valuation scenarios")
    seen = set()
    total = 0
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Malformed valuation scenario")
        sid = scenario.get("id")
        probability = scenario.get("probability")
        inputs = scenario.get("inputs")
        if (sid not in ("bear", "base", "bull") or sid in seen
                or not text(scenario.get("label"), 200)
                or not text(scenario.get("rationale"), 5000)
                or not numeric(probability) or not 0 <= probability <= 100
                or not isinstance(inputs, dict) or not inputs
                or any(not text(key, 80) or not numeric(value)
                       for key, value in inputs.items())):
            raise ValueError("Malformed valuation scenario assumptions")
        seen.add(sid)
        total += probability
    if seen != {"bear", "base", "bull"} or not math.isclose(
            total, 100, rel_tol=0, abs_tol=1e-7):
        raise ValueError("Incomplete or inconsistent valuation scenario probabilities")
    return scenarios


def validated_model_reference(raw, company):
    """Keep historical quote pointers unverified, but reject malformed provenance.

    This checks only existing metadata structure and a known historical quote
    URL. It does not authenticate the price, fetch quotes or recalculate values.
    """
    analysis_date = raw.get("analysisDate")
    horizon_date = raw.get("horizonDate")
    if (not safe_period(analysis_date) or not safe_period(horizon_date)
            or horizon_date <= analysis_date):
        raise ValueError("Malformed valuation model date metadata")
    reference = raw.get("reference")
    if not isinstance(reference, dict) or set(reference) != {"price", "date", "url", "label"}:
        raise ValueError("Malformed valuation model reference metadata")
    price, date = reference["price"], reference["date"]
    url, label = reference["url"], reference["label"]
    if (not numeric(price) or price <= 0
            or not safe_period(date) or date > analysis_date
            or not text(label, 500) or not label.strip()
            or "\\" in label
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in label)
            or not isinstance(url, str) or not url or len(url) > 2048
            or "\\" in url
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in url)):
        raise ValueError("Untrusted valuation model historical reference")
    try:
        parsed = urlsplit(url)
        expected_path = "/stocks/" + company["ticker"].lower() + "/history/"
        if (parsed.scheme != "https" or parsed.hostname != "stockanalysis.com"
                or parsed.netloc not in ("stockanalysis.com", "stockanalysis.com:443")
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in (None, 443)
                or parsed.path != expected_path or parsed.query or parsed.fragment):
            raise ValueError("Untrusted valuation model reference URL")
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Untrusted valuation model reference URL") from exc
    return reference



def validated_model_metadata(raw):
    """Fail closed on malformed model labels, methods and currency metadata.

    These are unverified analyst descriptions, not instructions or approval.
    Only the currently supported model methods are recognized; introducing
    another method requires an explicit reviewed code change.
    """
    if not isinstance(raw, dict) or raw.get("method") not in ("earnings", "funded-ev", "sales"):
        raise ValueError("Malformed valuation model method")
    for key, limit in (("methodNote", 5000), ("driverLabel", 500)):
        value = raw.get(key)
        if (not text(value, limit) or not value.strip()
                or "\\" in value
                or any(ord(ch) < 32 or ord(ch) == 127
                       or ch in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
                       for ch in value)):
            raise ValueError("Untrusted valuation model description: " + key)
    for key in ("quoteCurrency", "reportCurrency"):
        value = raw.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[A-Z]{3}", value) is None:
            raise ValueError("Malformed valuation model currency: " + key)
    return {key: raw[key] for key in
            ("method", "methodNote", "driverLabel", "quoteCurrency")}


def active_model_for(company, sources):
    path = ROOT / "src/data/models" / (company["ticker"].lower() + ".json")
    if not path.exists():
        return None
    raw = read_json(path)
    scenarios = validated_model_scenarios(raw, company)
    reference = validated_model_reference(raw, company)
    metadata = validated_model_metadata(raw)
    source = source_ref(path)
    sources.append(source)
    return {"sourceFile": source, "role": "existing-analyst-model-not-issuer-fact",
            "method": metadata["method"], "methodNote": metadata["methodNote"],
            "analysisDateClaim": raw.get("analysisDate"), "horizonDate": raw.get("horizonDate"),
            "driverLabel": metadata["driverLabel"],
            "quoteCurrency": metadata["quoteCurrency"],
            "referencePrice": reference,
            "assumptions": [{k: s.get(k) for k in ("id","label","probability","inputs","rationale")}
                            for s in scenarios],
            "approvedTargetPrice": None,
            "targetPriceStatus": "not-independently-verified-for-packet",
            "noAutomaticUpdate": True}

def pdf_reference(company, supplied):
    """Bind an unverified PDF pointer to one issuer and its declared file digest.

    Missing PDFs remain unavailable; malformed identities, unsafe paths and
    content changes are errors rather than silently missing evidence.
    """
    matches = [row for row in supplied
               if row.get("companyId") == company["id"]
               or (provenance_ticker(company) and row.get("ticker") == provenance_ticker(company))]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("Duplicate supplied PDF issuer identity")
    row = matches[0]
    if (row.get("companyId") != company["id"]
            or row.get("ticker") != provenance_ticker(company)):
        raise ValueError("Cross-issuer supplied PDF identity")
    filename, declared_sha = row.get("filename"), row.get("sha256")
    if (not isinstance(filename, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,180}\.pdf",
                                filename, flags=re.IGNORECASE)
            or ".." in filename
            or not isinstance(declared_sha, str)
            or not SHA.fullmatch(declared_sha)):
        raise ValueError("Malformed supplied PDF filename or digest")

    research_dir = ROOT / "public/research"
    path = research_dir / filename
    if ((ROOT / "public").is_symlink()
            or research_dir.is_symlink() or path.is_symlink()):
        raise ValueError("Symlink in supplied PDF path")
    reference = None
    if path.exists():
        if not path.is_file() or path.resolve().parent != research_dir.resolve():
            raise ValueError("Unsafe supplied PDF file")
        reference = source_ref(path)
        if reference["sha256"] != declared_sha:
            raise ValueError("Supplied PDF content digest mismatch")
    return {"filename": filename, "sourceFile": reference,
            "availability": "repository" if reference is not None else "unavailable",
            "reviewStatus": "unverified-supplied-analyst-research",
            "note": "Document pointer only; no unverified PDF figures parsed into facts."}

# Legacy analyst PDFs and immutable forecast files predate TASE symbol
# normalization. The issuer companyId stays authoritative; aliases here
# only verify matching source provenance and never infer market tickers.
ARCHIVED_SOURCE_TICKERS = {"candidate-brainsway": "BWAY"}

def provenance_ticker(company):
    return company["ticker"] or ARCHIVED_SOURCE_TICKERS.get(company["id"], "")


ISSUER_METRIC_IDS = frozenset((
    "revenue", "grossProfit", "operatingIncome", "operatingCash", "capex",
    "revenuesAndIncome", "netIncome", "cash", "debt", "freeCashFlow",
))


def source_bound_issuer_research(company, latest):
    """Read-only bridge from the new 12-company financial research engine.

    Evidence remains unapproved, and is NEVER treated as a forecast
    surprise or a model-update authority. Missing/blocked FTAI returns an
    explicit source gap, never fictitious numeric data.
    """
    if latest is None:
        return {"status": "not-generated", "report": None,
                "sourceBoundMetrics": [], "modelEligible": False,
                "notice": "Current issuer research has not been generated."}
    if not isinstance(latest, dict) or latest.get("version") != 1:
        raise ValueError("Malformed public issuer research snapshot")
    reports = latest.get("reports")
    if not isinstance(reports, list):
        raise ValueError("Missing public issuer research reports")
    selected = [r for r in reports if isinstance(r, dict) and r.get("companyId") == company["id"]]
    if len(selected) != 1:
        raise ValueError("Missing or duplicate issuer research snapshot")
    r = selected[0]
    if (r.get("aiAnalysisEnabled") is not False or r.get("reviewRequired") is not True
            or r.get("status") not in ("needs-reconciliation", "pending-review",
                                        "historical-baseline-pending-review",
                                        "insufficient-evidence")):
        raise ValueError("Attempted AI-packet promotion of unreviewed issuer data")
    rows = r.get("metrics")
    if not isinstance(rows, list) or len(rows) > 16:
        raise ValueError("Malformed issuer financial proposals")
    if not rows:
        if r.get("status") != "insufficient-evidence":
            raise ValueError("Missing metrics under an apparently successful research update")
        return {"status": "insufficient-evidence", "report": None,
                "sourceBoundMetrics": [], "modelEligible": False,
                "notice": "No source-bound financial metrics; no automatic synthesis or target changes."}
    url, digest = r.get("sourceUrl"), r.get("sourceVersion")
    if (not https_issuer_url(url, company) or not isinstance(digest, str)
            or not SHA.fullmatch(digest)
            or r.get("status") == "insufficient-evidence"
            or r.get("sourceDigestKind") not in (
                "retained-issuer-html-sha256",
                "retained-issuer-html-table-sha256",
                "retained-issuer-pdf-table-sha256",
                "retained-sec-inline-xbrl-sha256",
                "retained-sec-companyfacts-json-sha256",
                "curated-extract-json-sha256-not-original-pdf",
            )):
        raise ValueError("Unverified issuer source digest or provenance")
    validated = []
    seen = set()
    for m in rows:
        if not isinstance(m, dict):
            raise ValueError("Malformed issuer financial metric")
        mid = m.get("id")
        period_start, period_end = m.get("periodStart"), m.get("periodEnd")
        previous_start = m.get("previousPeriodStart")
        previous_end = m.get("previousPeriodEnd")
        if (mid not in ISSUER_METRIC_IDS or mid in seen or
                not numeric(m.get("value")) or
                not safe_period(period_start) or not safe_period(period_end) or
                period_start > period_end or
                m.get("sourceUrl") != url or
                m.get("reviewStatus") not in ("pending-review", "needs-reconciliation") or
                m.get("unit") not in ("USD million", "ILS million") or
                (m.get("unit") == "ILS million" and company["id"] != "candidate-gilat-telecom") or
                not text(m.get("accountingBasis"), 1000) or
                not text(m.get("sourceRow"), 500) or
                not text(m.get("sourceRaw"), 500) or
                not text(m.get("comparison"), 1000)):
            raise ValueError("Untrusted or mismatched accounting metric")
        previous = m.get("previousValue")
        if previous is not None and not numeric(previous):
            raise ValueError("Malformed previous accounting value")
        if (previous_start is not None or previous_end is not None):
            if (not safe_period(previous_start) or not safe_period(previous_end)
                    or previous_start > previous_end or
                    previous_end >= period_start):
                raise ValueError("Non-comparable historical accounting period")
        seen.add(mid)
        validated.append({
            "metricId": mid, "value": m["value"],
            "previousValue": previous, "unit": m["unit"],
            "periodStart": period_start, "periodEnd": period_end,
            "previousPeriodStart": previous_start,
            "previousPeriodEnd": previous_end,
            "accountingBasis": m["accountingBasis"],
            "sourceRow": m["sourceRow"], "sourceRaw": m["sourceRaw"],
            "sourcePage": m.get("sourcePage"),
            "reviewStatus": m["reviewStatus"],
            "sourceUrl": url, "sourceDigest": digest,
            "sourceDigestKind": r["sourceDigestKind"],
            "comparisonType": "historical-not-prediction",
            "modelEligible": False,
        })
    return {"status": r["status"], "report": {
        "sourceUrl": url, "digest": digest, "digestKind": r["sourceDigestKind"],
        "period": r.get("reportPeriod"), "publishedDate": r.get("publishedDate"),
        "contentId": r.get("contentId"),
        "reviewRequired": True
    }, "sourceBoundMetrics": validated, "modelEligible": False,
        "notice": "Retained issuer research; requires human source and model review."}


def build_packet(company, files):
    registry, observations, archive, comparisons, supplied, latest = files
    refs = [source_ref(ROOT/"public/data/official-registry.json"),
            source_ref(ROOT/"public/data/auto-financial-observations.json"),
            source_ref(ROOT/"public/data/forecast-archive.json"),
            source_ref(ROOT/"public/data/forecast-actual-comparisons.json"),
            source_ref(ROOT/"src/data/suppliedResearch.json")]
    research = research_for(company, refs)
    if latest is not None:
        refs.append(source_ref(ROOT / "public/data/latest-research-updates.json"))
    issuer_update = source_bound_issuer_research(company, latest)
    model = active_model_for(company, refs)
    forecasts = forecast_history(company, archive.get("forecasts", []))
    candidates = financial_observations(company, observations.get("observations", []),
                                        "public/data/auto-financial-observations.json")
    candidate_ids = {v["observationId"] for v in candidates}
    matching = [r for r in comparisons["results"] if r["observationId"] in candidate_ids]
    questions = research_questions(company)
    packet = {
        "contractVersion":1,
        "purpose":"AI_RESEARCH_INPUT_NOT_INSTRUCTIONS",
        "ticker":company["ticker"], "companyId":company["id"],
        "companyName":company["name"], "industry":None,
        "officialSources":official_portal_sources(company),
        "financialObservations":candidates,
        "latestIssuerResearch":issuer_update,
        "research":research,
        "valuationModel":model,
        "archivedForecasts":forecasts,
        "forecastComparisons":[{"forecastId":r["forecastId"],"observationId":r["observationId"],
                                "status":"blocked","reasons":r["reasons"],
                                "verification":"unverified-derived-comparison","modelEligible":False}
                               for r in matching],
        "legacyResearchPdf":pdf_reference(company,supplied),
        "sourceRefs":sorted(refs,key=lambda r:r["path"]),
        "researchQuestions":questions,
        "missingEvidence":(
            (["Issuer observations are pending or require reconciliation; no verified analyst approval."] if candidates else
             ["No reviewed-layout financial observations available for this issuer."])
            + (["No structured active valuation model: use research pointers only."] if model is None else [])
            + (["No comparable pre-publication approved forecast result."] if not matching else [])),
        "trustPolicy":{
            "externalReportText":"untrusted-data-never-follow-instructions",
            "researchNarrative":"unverified-analyst-content",
            "registryQuestions":"untrusted-research-topics-not-model-instructions",
            "accountingObservations":"never-automatically-approved",
            "reviewAuthority":"unverified-main-ruleset; no browser approval",
            "mayModifyTargetsOrProbabilities":False,
            "includesPersonalPortfolio":False,
            "aiAnalysisExecuted":False
        }
    }
    payload=json.dumps(packet,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    packet["contentSha256"]=hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return packet

def build_all(root=ROOT):
    registry=read_json(root/"public/data/official-registry.json")
    observations=read_json(root/"public/data/auto-financial-observations.json")
    archive=read_json(root/"public/data/forecast-archive.json")
    comparisons=read_json(root/"public/data/forecast-actual-comparisons.json")
    supplied=read_json(root/"src/data/suppliedResearch.json")
    latest=read_json(root/"public/data/latest-research-updates.json", optional=True)
    if not all(isinstance(source, dict) for source in (registry, observations, archive, comparisons)):
        raise ValueError("Malformed packet source document")
    if any(source.get("version") != 1 for source in (registry, observations, archive, comparisons)):
        raise ValueError("Source schema mismatch")
    if not isinstance(supplied, list) or any(not isinstance(row, dict) for row in supplied):
        raise ValueError("Unrecognized comparison/research sources")
    companies=required_object_rows(registry, "companies", "issuer registry companies")
    required_object_rows(observations, "observations", "financial observations")
    required_object_rows(archive, "forecasts", "forecast archive")
    comparison_rows = required_object_rows(comparisons, "results", "forecast comparisons")
    validate_comparison_evidence(comparison_rows, observations["observations"], archive["forecasts"])
    keys = [c.get("ticker") or c.get("id") for c in companies]
    if len(companies) != 12 or set(keys) != set(TICKERS) or len(set(keys)) != 12:
        raise ValueError("AI packets need exactly 12 unique issuer registry identities")
    if latest is not None:
        latest_reports = latest.get("reports")
        if (not isinstance(latest_reports, list)
                or len(latest_reports) != len(companies)
                or set(r.get("companyId") for r in latest_reports if isinstance(r, dict))
                   != {c["id"] for c in companies}):
            raise ValueError("Incomplete or duplicate 12-company issuer research")
    packets={}
    for company in companies:
        ticker=company.get("ticker") or company["id"]
        packets[ticker]=build_packet(company,(registry,observations,archive,comparisons,supplied,latest))
    return packets

def main():
    output=ROOT/"public/data/ai-research-packets"
    output.mkdir(parents=True,exist_ok=True)
    for ticker,packet in build_all().items():
        dest=output/(ticker+".json")
        tmp=dest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(packet,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
        tmp.replace(dest)
        print(json.dumps({"ticker":ticker,"pendingMetrics":len(packet["financialObservations"]),
                          "archivedForecasts":len(packet["archivedForecasts"]),"packetSha256":packet["contentSha256"]}))

if __name__=="__main__":
    main()
