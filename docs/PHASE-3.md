# Phase 3 operating contract

Existing personal storage version 1, holdings, notes and backups are unchanged.
Read flags use a separate local key `pulse-read-news-v1`; unrelated flags remain
local. These are not synced to GitHub and are not notification preferences.

## Rating evidence-3.2 (supersedes evidence-3.1)

The prior rule matched event keywords and assigned medium/low, with no separate
source reliability or company relevance. It has been replaced in the visible
feed by `scripts/rating.py`: separate event score, source authority, relevance,
evidence basis and confidence. The version, reason and exact source URLs are
stored per item. Opinion/price-target content remains low. Headline-only events
are capped at 55/100 and cannot trigger a high alert. Only a verified official
metadata record can pass the high-event gate. No score predicts price direction.
Syndicated/near-identical titles are grouped conservatively; source count never
increases independent confirmations. Similar events with different titles may
remain separate. Company identity exclusions still apply before scoring.
Version 3.2 adds explicit exclusions for another investor's purchase of shares
and for announcements of future earnings dates. Neither is treated as an
acquisition by the company or publication of actual financial results.

## Daily windows and industry context

Actions polls at UTC :17 and :47 using standard Ubuntu, including weekends.
GitHub schedules can be late, disabled by inactivity or canceled by newer runs.
No exact-time/realtime delivery is promised. The latest eligible daily window
ends at 13:00 Asia/Jerusalem and starts exactly 24 elapsed hours earlier, so a
DST-transition window does not necessarily start at 13:00 local the previous day.
Selection is [start,end) by publication timestamp; collection timestamps never
substitute for missing publication dates. Undated items are shown separately.
The window and actual generation time are displayed. A published daily ID is
immutable on reruns; late discoveries appear in news, not a duplicate briefing.
An explicit query/rating version correction may update that same ID while
preserving its first generation time and incrementing a visible revision;
notification deduplication still uses the same daily ID.
If the scheduler was absent for several days only the latest eligible window
is produced; missed days are not silently backfilled as if produced on time.

`industry-registry.json` maps reviewed company business contexts to Hebrew and
English queries. Industry items retain their own industry IDs, source status,
title, publisher, publication and collection times. They are not attributed to
the company. Each company section explains the relevance as research context.
Failures preserve previous items; a failed search cannot become "no news".

## Hebrew summarization feasibility

The isolated `Hebrew summary feasibility` workflow tests the Apache-2.0
Qwen/Qwen2.5-0.5B-Instruct model on CPU, using actual company/industry headlines.
No paid hosted inference is used. Safetensors and trust_remote_code=False avoid
executing downloaded model repository code. The model card does not establish
Hebrew financial-summary quality. Outputs must be reviewed for fluent Hebrew,
faithfulness, citations, uncertainty and no unsupported details before any
integration. Source text is explicitly untrusted data. The first run failed
on an industry RSS 503 before inference; a separate retry isolates that failure.
Until a successful quality review, the UI explicitly offers a Hebrew metadata
template with original headline links and questions, **not an AI article summary**.
This is a material unfinished capability when no model passes the gate.

Actual quality review: Qwen2.5-0.5B completed in 30.09 script seconds, but
answered in English without citations and changed Crusoe to Crispy. Qwen3-1.7B
completed in 130.63 script seconds but copied English company headlines and
produced incoherent, unsupported industry Hebrew. Both use Apache-2.0 licenses
and were rejected. Timings exclude dependency installation. Exact revisions
and actual Actions runs are in `public/data/summary-feasibility.json`.
This does not prove every other free model would fail; no tested candidate
passed this quality gate.

## Earnings

The calendar covers all eleven companies, with confirmed, estimated and
unannounced/unknown statuses. Unknown is not inferred to mean the issuer has
not published when a source is inaccessible. Dates come from reviewed official
IR releases or an explicitly issuer-distributed press release, not last year's
calendar. No speculative estimate is seeded. Sandisk's stated call time remains
an earnings-call event, not the publication time of financial results.

`scripts/earnings.py` checks bounded official index/release pages, extracts only
metadata, never executes script or scraped text, and follows only same-company
allowlisted HTTPS hosts. Up to three release pages per issuer are checked.
PDFs, dynamic pages and unavailable sources require manual review; source status
is visible and prior valid events remain. A date-change revision keeps the same
company/report-period identity. Only an explicit results publication qualifies
as results-published, not an announcement of future results or conference call.
First detections of historical releases are not historical new-event alerts.

## Notifications and validation

See [Android setup and private configuration](NOTIFICATIONS.md). Notification
planning and transport are separate from collection and Pages. A missing Secret
does not break Google News. Public feed artifacts never include notification
configuration. The opaque intent ledger is cached before one send attempt;
an ambiguous timeout cannot safely be retried as guaranteed exactly-once.

Python tests use labeled simulated sources for evidence gates, unrelated items,
syndication, DST/late windows, date changes, call-vs-results identification,
reminders, quiet hours and deduplication. Node/browser schema/provenance checks
validate the actual feed. Manual/code releases additionally run headless Chromium
at 320/390/430, 200% text, read flags, modal and simulated visual keyboard viewport.
Screenshots are retained as `mobile-emulation-evidence`. This is not a physical
Android keyboard or locked-device ntfy receipt test. Device receipt requires the
owner's one-time installation, secrets and observation, and remains unverified
until that observation is reported.

## Persisted snapshot compatibility and rerating

The collector validates a retained `evidence-3.1` snapshot with a dedicated,
bounded prior-version schema before using it as input. It does not relabel old
ratings as 3.2 or skip source/provenance checks. New published intelligence must
still pass the strict current schema after all retained items are rerated.
Unknown and mixed per-item rating versions are rejected. Historical daily
publications retain their own rating version and revision history.

SEC periodic report detection uses the retained form (`10-K`, `10-Q`, `20-F`,
`40-F`, including amendments), not a previously generated classification that
was overwritten during enrichment. A repeat run must retain the same evidence
rating. Regression checks cover persisted-input compatibility, corrupt source
attribution, rating evidence, missing ratings and repeat SEC enrichment.
