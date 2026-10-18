# Public headline discovery

The Nebius feasibility gate was tested on standard Ubuntu GitHub Actions, not
in the browser: https://github.com/roeeazaria55/pulse-investment-research./actions/runs/39128517271
Google News RSS returned 99 candidate titles on 2026-10-18. One sample, the
October 13 NVIDIA Run:ai announcement, was checked against Nebius's own publication:
https://nebius.com/blog/posts/nvidia-run-ai-open-source-nebius-applications
GDELT DOC 2.0 returned HTTP 429 after bounded retries. It remains disabled.
The probe can be manually repeated with the `Nebius news feasibility` workflow.
Enabling a failed provider requires another actual runner test and review.

`public/data/news-registry.json` records company identity, official evidence,
English/Hebrew aliases, context, exclusions and provider policy/proof URLs.
These are identities for headline search, independently of the stock listing,
share class, exchange or CIK in `registry.json`. No personal watchlist is sent
to Actions. Unknown private companies get a local web search link only.

Only the two explicitly allowlisted HTTPS provider endpoints can be fetched.
Redirects are rechecked (maximum two); no publisher URLs, article bodies,
paywalls, alternate endpoints or Google redirect decoding are fetched. Google
RSS is a public endpoint without an availability SLA. Review of Google's terms
does not grant rights to publisher content: only attributed original headlines
and links are displayed, no RSS descriptions, summaries or article text.
Stop on 401/403/451; retry network errors, 429 and 5xx at most once, with
backoff. Each request has socket/total limits and a 2 MiB streaming cap.
Companies are requested sequentially with a three-second pause. The workflow
has a hard execution limit. No fetched text becomes a command or file path.

The collector searches a 30-day window and applies title-only identity/context
rules (conservative; may miss relevant articles). Gilat Telecom explicitly
excludes Gilat Satellite Networks. IREN requires cloud/AI/mining context and
excludes the Italian utility. Meta and Lemonade require business context.
Classification only matches explicit event terms in the title, never sentiment,
investment advice or fabricated AI analysis. The original title is preserved.
Up to 20 deduplicated records per company are selected per run. Stable IDs hash
company identity and normalized title (publisher suffix removed); URL variants
and syndicated copies of the exact title are collapsed. Different titles for
the same story can still remain; renamed stories may receive a new ID.

`schemas/discovery.schema.json` documents the additive v2 fields `articles` and
`discovery`; the original `news` array remains SEC-only. Both browser and CI
validate schemas and provenance. The browser merges validated articles into
the visible feed. `publisher` is RSS source attribution, not independently
verified editorial authorship. `discoveryProvider` and `linkKind` distinguish
Google News wrapper links from publisher links. Google publication dates are
used only when supplied with a timezone; missing/invalid dates remain null.
GDELT `seendate` is discovery time and is never a publication timestamp.
`collectedAt` is the first successful PULSE collection time, preserved on repeats.

Per-company/provider statuses distinguish results, zero-results and failures,
with lastAttemptAt/lastSuccessfulAt/error/count/rejectedCount. Failure preserves
valid prior records and timestamps. A failed search cannot become "no new items".
Full discovery success covers enabled discovery sources only; disabled GDELT
and supplemental SEC failures remain visible separately. The existing top-level
SEC status is never relabeled as successful news discovery.

Seen IDs and morning/evening briefing slots persist in the public feed alongside
the selected public ingestion state commit. Jerusalem time uses IANA timezone
data, including DST. Briefings are metadata templates and merge IDs within a
slot without repeated announcements. Unknown-date records cannot be aged by
publication time; the total feed is bounded at 600 items and processing state
at 100,000 IDs (manual compaction thereafter). Historical briefs may refer to
records that have expired from the retained window.

`Publish PULSE` independently discovers headlines, gathers supplemental SEC,
validates, tests and builds, then explicitly deploys that exact artifact.
Only two selected public JSON files are committed. Collection, state writing
and Pages deployment have separate minimal permissions. Untrusted PR checks
cannot collect, write or deploy. UTC schedules at :23 cover Jerusalem DST
morning/evening windows; completed successful slots prevent duplicate publishing.
GitHub schedules may be delayed or disabled after repository inactivity;
use Run workflow to recover. This is not a guaranteed realtime service.

"Not related to company" reports are local browser flags with an undo action;
they are not sent to maintainers or used to alter the public feed. Portfolio,
research notes and backups remain private in the browser. Headlines do not
mean PULSE has read the full article. Search links remain available offline
in the application shell, but opening an external website needs connectivity.
