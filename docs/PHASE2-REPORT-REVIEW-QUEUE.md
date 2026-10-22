# Phase 2 — persistent report review queue

The existing scheduled publisher already discovers approved issuer URLs, reads
bounded report bodies, stores tables/XBRL candidates and preserves failed-read
history in `public/data/report-intake.json`. This change **does not replace**
that collector and does not assert that HTTP 403 sources are fixed.

`scripts/report_review_queue.py` now runs after collection in the production
GitHub Pages pipeline and in PR CI. It writes
`public/data/report-review-queue.json`, which is persisted with the other
public snapshots. A record is keyed by company ID, source document ID and
SHA-256 of the exact bytes that were read. Re-reading the same version does
not generate another new pending version. Reading changed bytes creates a new
pending version while retaining the earlier version, bounded to 180 records.

All versions stay **pending-review** and include issuer URL, original hash,
collection/publication metadata when available, source table and structured
XBRL fact counts, a possible refresh error and a source revision indicator.
No inferred accounting units, quarter/year conversions, price targets or
forecasts are written. A date from an issuer index remains unverified
metadata, not an accounting period. Where a report source fails or defers,
the failure is separately recorded; it is not evidence of nonpublication.

The first production run initializes a backlog from already-collected reports.
Its `newPendingVersions` count does **not** mean these reports were newly
published on the same day. Future runs detect newly *observed* document
content, not a guaranteed earnings release event. When the collector cannot
access an official URL or a report is not in the metadata registry, no
automatic retrieval is claimed.

## Validation

`python3 -m unittest discover -s scripts -p 'test_*.py'` covers duplicate
reads, same-URL revisions, missing document/failure states, issuer-allowlist
checks and the requirement that manually approved/edited state cannot silently
be carried forward as an approval. PR CI runs the queue builder after the
real collector, uploads its JSON as an evidence artifact and builds the app.
The scheduled publisher persists the review queue alongside the intake
snapshot, and ignores generated state-only commits.

## Still required

- Review source-specific accounting mappings and period/definition bridges.
- Promote **approved** metrics via a separately audited workflow; never infer
  an approval from a queue entry.
- Add NBIS/DLO reviewed issuer adapters and prospective forecast evaluation.
- Improve availability for official sources returning HTTP 403 through
  documented compliant retrieval methods.

This milestone is a durable source-version review inbox, **not** unattended
financial-statement extraction or automatic valuation updates.
