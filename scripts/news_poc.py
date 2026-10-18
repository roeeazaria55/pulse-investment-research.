"""Read-only feasibility probe. Never updates the application's public feed."""
import datetime as dt
import email.utils
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

LIMIT = 2 * 1024 * 1024
ENDPOINTS = {
    "google-news": "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": '"Nebius" when:30d', "hl": "en-US", "gl": "US", "ceid": "US:en"}),
    "gdelt": "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({
        "query": 'Nebius', "mode": "artlist", "format": "json", "timespan": "30d",
        "maxrecords": "50", "sort": "datedesc"}),
}

def allowed(url):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == "https" and not p.username and not p.password and p.port in (None, 443)
            and ((p.hostname == "news.google.com" and p.path == "/rss/search")
                 or (p.hostname == "api.gdeltproject.org" and p.path == "/api/v2/doc/doc")))

class Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError("Redirect target not approved")
        if getattr(req, "redirect_count", 0) >= 2:
            raise ValueError("Too many redirects")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        redirected.redirect_count = getattr(req, "redirect_count", 0) + 1
        return redirected

def fetch(url):
    if not allowed(url):
        raise ValueError("Target not approved")
    opener = urllib.request.build_opener(Redirects())
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "PULSE-News-Feasibility/1.0 (+https://github.com/roeeazaria55/pulse-investment-research./issues)",
                "Accept": "application/rss+xml, application/xml, application/json, text/xml"})
            started = time.monotonic()
            with opener.open(req, timeout=20) as response:
                chunks, size = [], 0
                while True:
                    if time.monotonic() - started > 30:
                        raise TimeoutError("Response exceeded total time limit")
                    chunk = response.read(32768)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > LIMIT:
                        raise ValueError("Response exceeds 2 MiB")
                    chunks.append(chunk)
                return b"".join(chunks)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 451):
                raise
            if exc.code != 429 and exc.code < 500:
                raise
            if attempt == 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 1:
                raise
        time.sleep(2 ** (attempt + 1))

def safe_link(value):
    p = urllib.parse.urlsplit(value or "")
    return value if p.scheme in ("http", "https") and p.hostname and not p.username and not p.password else None

def parse_google(body, required_term="nebius"):
    if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise ValueError("DTD/entity declarations not accepted")
    root = ET.fromstring(body)
    if root.tag != "rss":
        raise ValueError("Expected RSS")
    result = []
    for item in root.findall("./channel/item")[:100]:
        title = item.findtext("title", "").strip()
        link = safe_link(item.findtext("link"))
        if (required_term and required_term not in title.lower()) or not link:
            continue
        raw_date = item.findtext("pubDate")
        publication = None
        if raw_date:
            try:
                parsed = email.utils.parsedate_to_datetime(raw_date)
                if parsed.tzinfo:
                    publication = parsed.isoformat()
            except (ValueError, TypeError):
                pass
        result.append({"title": title, "publisher": item.findtext("source"), "url": link,
                       "linkKind": "google-news-redirect", "publishedAt": publication,
                       "rawPublicationDate": raw_date, "discoveredAt": None})
    return result

def parse_gdelt(body, required_term="nebius"):
    data = json.loads(body)
    if not isinstance(data, dict) or not isinstance(data.get("articles"), list):
        raise ValueError("Expected GDELT articles array")
    return [{"title": a["title"], "publisher": a.get("domain"), "url": safe_link(a.get("url")),
             "linkKind": "publisher", "publishedAt": None, "discoveredAt": a.get("seendate")}
            for a in data["articles"][:50]
            if isinstance(a, dict) and isinstance(a.get("title"), str)
            and (not required_term or required_term in a["title"].lower()) and safe_link(a.get("url"))]

def main():
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    report = {"company": "Nebius Group", "windowDays": 30, "collectedAt": now,
              "runUrl": os.getenv("GITHUB_SERVER_URL", "") + "/" + os.getenv("GITHUB_REPOSITORY", "")
                        + "/actions/runs/" + os.getenv("GITHUB_RUN_ID", ""), "providers": []}
    for provider, endpoint in ENDPOINTS.items():
        try:
            body = fetch(endpoint)
            items = (parse_google if provider == "google-news" else parse_gdelt)(body)
            report["providers"].append({"provider": provider, "status": "results" if items else "zero-results",
                                        "queryUrl": endpoint, "items": items, "count": len(items)})
        except Exception as exc:
            report["providers"].append({"provider": provider, "status": "failed", "queryUrl": endpoint,
                                        "error": str(exc)[:500], "items": [], "count": 0})
        time.sleep(2)
    report["hasCandidateResults"] = any(p["count"] > 0 for p in report["providers"])
    Path("work").mkdir(exist_ok=True)
    Path("work/news-poc.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PULSE_POC_RESULT=" + json.dumps(report, ensure_ascii=False))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write("## Nebius discovery feasibility (not production ingestion)\n\n")
            for p in report["providers"]:
                file.write(f"- {p['provider']}: {p['status']}; {p['count']} candidate headlines.\n")
            file.write("\nInspect the JSON artifact and company relevance before integrating. "
                       "GDELT seendate is discovery time, not publication time. No article bodies collected.\n")

if __name__ == "__main__":
    main()
