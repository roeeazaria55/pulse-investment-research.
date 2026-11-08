"""Public headline discovery only; company identity is independent of listing identity."""
import datetime as dt
import hashlib
import json
import re
import time
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo
from news_poc import fetch, parse_google, parse_gdelt, safe_link

ROOT = Path("public/data")

def normalized(text):
    return re.sub(r"[^a-z0-9\u0590-\u05ff]+", " ", text.casefold()).strip()

def contains(text, term):
    return (" " + normalized(term) + " ") in (" " + normalized(text) + " ")

def relevant(title, company):
    if any(contains(title, term) for term in company["exclude"]):
        return False
    return (any(contains(title, term) for term in company["distinctiveAliases"])
            or (any(contains(title, term) for term in company["aliases"])
                and any(contains(title, term) for term in company["context"])))

def endpoint(provider, company):
    if provider == "google-news":
        return "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": company["query"] + " when:30d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
    if provider == "gdelt":
        return "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({
            "query": company["gdeltQuery"], "mode": "artlist", "format": "json",
            "timespan": "30d", "maxrecords": "50", "sort": "datedesc"})
    raise ValueError("Unapproved provider")

def classify(title):
    # Headline rules only. No inferred sentiment or reading of article bodies.
    if any(contains(title, x) for x in ["earnings", "results", "acquires", "acquisition", "lawsuit", "דוחות", "תוצאות", "רכישה"]):
        return {"rule": "headline-event-term", "reason": "מילת אירוע בכותרת המקור (תוצאות, רכישה או הליך משפטי); לא נקראה הכתבה המלאה."}, "medium"
    return {"rule": "company-headline-match", "reason": "שם חברה והקשר תואמים בכותרת בלבד; לא נקראה הכתבה המלאה."}, "low"

def article(item, company, provider, now):
    title = item["title"]
    publisher = item.get("publisher") or urllib.parse.urlsplit(item["url"]).hostname
    suffix = " - " + publisher
    identity_title = title[:-len(suffix)] if title.endswith(suffix) else title
    digest = hashlib.sha256((company["id"] + "|" + normalized(identity_title)).encode()).hexdigest()[:32]
    classification, importance = classify(title)
    return {"id": "article:" + digest, "securityId": company["id"], "ticker": company["displayTicker"],
            "company": company["name"], "headline": title, "originalTitle": title,
            "sourceUrl": item["url"], "publisher": publisher, "sourceName": publisher,
            "sourceId": provider + ":" + company["id"], "discoveryProvider": provider,
            "linkKind": item["linkKind"], "publishedAt": item.get("publishedAt"),
            "discoveredAt": item.get("discoveredAt"), "collectedAt": now,
            "importance": importance, "classification": classification, "summary": "",
            "summaryKind": "metadata-only", "demo": False, "documentId": digest}

def retained_article(item, companies, providers):
    """Rebuild persisted headline records as unverified discovery metadata.

    pulse-data is a writable collection snapshot, not an authority for
    verifiedOfficial, ratings, SEC identities, summaries or new fields.
    Reject mismatched identities instead of carrying them into enrichment.
    This is structural validation, NOT authentication of a publisher.
    """
    if not isinstance(item, dict):
        return None
    security_id = item.get("securityId")
    provider = item.get("discoveryProvider")
    if not isinstance(security_id, str) or not isinstance(provider, str):
        return None
    company = companies.get(security_id)
    if not company or provider not in providers or provider not in ("google-news", "gdelt"):
        return None
    if item.get("sourceId") != provider + ":" + company["id"]:
        return None
    title = item.get("headline")
    if (not isinstance(title, str) or not title.strip() or len(title) > 1000
            or item.get("originalTitle") != title or not relevant(title, company)):
        return None
    url = item.get("sourceUrl")
    if not isinstance(url, str) or len(url) > 2048:
        return None
    try:
        if safe_link(url) != url:
            return None
    except ValueError:
        return None
    kind = "google-news-redirect" if provider == "google-news" else "publisher"
    if item.get("linkKind") != kind:
        return None
    publisher = item.get("publisher")
    if publisher is not None and (not isinstance(publisher, str) or len(publisher) > 250):
        return None
    discovered = item.get("discoveredAt")
    if discovered is not None and (not isinstance(discovered, str) or len(discovered) > 80):
        return None
    for stamp in (item.get("collectedAt"), item.get("publishedAt")):
        if stamp is None:
            continue
        if not isinstance(stamp, str):
            return None
        try:
            parsed = dt.datetime.fromisoformat(stamp)
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                return None
        except (ValueError, TypeError, OverflowError):
            return None
    if not item.get("collectedAt"):
        return None
    rebuilt = article({"title": title, "url": url, "publisher": publisher,
                       "linkKind": kind, "publishedAt": item.get("publishedAt"),
                       "discoveredAt": discovered}, company, provider, item["collectedAt"])
    return rebuilt if rebuilt["id"] == item.get("id") else None


def collect(registry, previous, now, getter=fetch, pause=time.sleep):
    old = previous.get("discovery", {})
    companies = {c["id"]: c for c in registry["companies"]}
    providers = {p["id"] for p in registry["providers"]}
    prior_items = [clean for item in previous.get("articles", [])
                   if (clean := retained_article(item, companies, providers)) is not None]
    old_seen = old.get("seenIds", [])
    if not isinstance(old_seen, list) or len(old_seen) > 100000:
        raise ValueError("Invalid discovery history; manual review required")
    seen = {v for v in old_seen if isinstance(v, str) and re.fullmatch(r"article:[0-9a-f]{32}", v)}
    seen.update(a["id"] for a in prior_items)
    if len(seen) > 100000:
        raise ValueError("Discovery state exceeds limit; manual compaction required")
    by_id = {a["id"]: a for a in prior_items}
    statuses, new_ids = [], []
    for provider in registry["providers"]:
        if not provider["enabled"]:
            continue
        for company in registry["companies"]:
            old_status = next((s for s in old.get("sources", [])
                               if s["provider"] == provider["id"] and s["securityId"] == company["id"]), {})
            url = endpoint(provider["id"], company)
            status = {"provider": provider["id"], "securityId": company["id"], "name": company["name"],
                      "queryUrl": url, "lastAttemptAt": now, "lastSuccessfulAt": old_status.get("lastSuccessfulAt"),
                      "status": "failed", "error": None, "count": 0, "newCount": 0, "rejectedCount": 0, "rejectedExamples": []}
            try:
                body = getter(url)
                candidates = parse_google(body, required_term=None) if provider["id"] == "google-news" else parse_gdelt(body, required_term=None)
                unique = {}
                for candidate in candidates:
                    if not relevant(candidate["title"], company):
                        status["rejectedCount"] += 1
                        if len(status['rejectedExamples'])<2:
                            status['rejectedExamples'].append({'title':candidate['title'],'publisher':candidate.get('publisher'),'reason':'לא עמד בכללי שם והקשר של החברה; לא צורף לפיד. זו פסילה שמרנית, לא קביעה שנקראה הכתבה.'})
                        continue
                    pub = candidate.get("publishedAt")
                    if pub:
                        age = (dt.datetime.fromisoformat(now) - dt.datetime.fromisoformat(pub)).total_seconds()
                        if age > 30 * 86400 or age < -300:
                            status["rejectedCount"] += 1
                            continue
                    item = article(candidate, company, provider["id"], now)
                    unique.setdefault(item["id"], item)
                # Stable per-company cap; prefer known publication dates, never substitute collection time.
                items = sorted(unique.values(), key=lambda a: a["publishedAt"] or "", reverse=True)[:20]
                for item in items:
                    if item["id"] not in seen:
                        new_ids.append(item["id"])
                        status["newCount"] += 1
                    # Preserve first collection timestamp when the same item reappears.
                    by_id.setdefault(item["id"], item)
                    seen.add(item["id"])
                status.update(status="results" if items else "zero-results", count=len(items), lastSuccessfulAt=now)
            except Exception as exc:
                status["error"] = str(exc)[:300]
            statuses.append(status)
            pause(3)
    # Retain valid previous items on failure. Prune only by an explicit publisher date.
    cutoff = dt.datetime.fromisoformat(now) - dt.timedelta(days=60)
    items = [a for a in by_id.values() if not a["publishedAt"] or dt.datetime.fromisoformat(a["publishedAt"]) >= cutoff]
    items.sort(key=lambda a: a["publishedAt"] or a["collectedAt"], reverse=True)
    items = items[:600]
    working = sum(s["status"] != "failed" for s in statuses)
    complete = bool(statuses) and working == len(statuses)
    local = dt.datetime.fromisoformat(now).astimezone(ZoneInfo("Asia/Jerusalem"))
    slot = local.strftime("%Y-%m-%d") + (":morning" if local.hour < 17 else ":evening")
    prior_brief = next((b for b in old.get("briefings", []) if b["id"] == slot), {})
    briefing = {"id": slot, "generatedAt": now, "timezone": "Asia/Jerusalem",
                "itemIds": list(dict.fromkeys(prior_brief.get("itemIds", []) + new_ids))[:220],
                "questions": ["האם הכותרת מגובה בפרסום המקורי?", "מה השתנה ומה מחייב קריאת כתבה מלאה?", "האם המידע משנה את תזת ההשקעה?"]}
    discovery = {"version": 1, "registry": registry, "lastAttemptAt": now,
                 "lastSuccessfulAt": now if complete else old.get("lastSuccessfulAt"),
                 "status": "complete" if complete else "partial" if working else "failed",
                 "sources": statuses, "newCount": len(new_ids), "noNewItems": working > 0 and not new_ids,
                 "seenIds": sorted(seen), "briefings": [briefing] + [b for b in old.get("briefings", []) if b["id"] != slot][:27]}
    return {"articles": items, "discovery": discovery}

if __name__ == "__main__":
    registry = json.loads((ROOT / "news-registry.json").read_text(encoding="utf-8"))
    previous = json.loads((ROOT / "feed.json").read_text(encoding="utf-8"))
    result = collect(registry, previous, dt.datetime.now(dt.timezone.utc).isoformat())
    Path("work").mkdir(exist_ok=True)
    Path("work/discovery.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["discovery"]["status"], "sources": result["discovery"]["sources"]}, ensure_ascii=False))
