# PULSE v1 — release candidate, evidence, operator playbook

This document describes **existing code paths**, not proof that the integration
branch has been published. PR #60 must not be merged into `main` without the
owner's explicit approval. Do not start a paid OpenAI API request.

## Supported, source-backed daily workflow

Open the installed PWA, select Research, choose a company, read the full
previously supplied research and Bear/Base/Bull model, then open the latest
research update on the Overview tab. DLO Q2 2026 uses a retained issuer HTML
report with an exact report ID, SHA-256, URL and publication date. Its extracted
observations require reconciliation and are **not** approved financial facts.
IREN FY2026 vs FY2025 uses a bounded curated official issuer table extract,
with raw cells and issuer PDF page pointers. The curated JSON digest is **not**
the original PDF hash. Historical FY2026 growth is **not** a surprise relative
to the October 2026 PULSE model.

All 12 registered companies have source-index, document-fetch and research
status. **11/12 now have source-bound financial observations** marked
`pending-review`: NBIS, META, DLO, LMND, SNDK, IREN, Next Vision (FY2025
historical), **Enlight** (Q2 2026 actual IFRS revenues USD 165.990m vs
116.117m; separate total revenues+tax benefits USD 209.691m vs 134.978m),
BrainsWay, **Gilat Telecom Global** (Q2 2026 NIS revenue 71.446m vs
66.508m; gross profit 21.025m vs 19.660m) and SMCI.

The original Enlight 34-page official earnings PDF and Gilat 64-page official
Hebrew Q2 financial PDF were actually downloaded in the PR source-probe,
content-SHAed and matched to issuer source-page text (without OCR). For
Gilat, original revenue table is on PDF page 6; source is in **ILS thousands**
and normalized to **ILS million**. For Enlight, Appendix 1 table is PDF
page 16; IFRS revenue excludes the U.S. tax benefits included in a separately
identified combined measure. Both are pending human review, not automatic
earnings surprises or model updates.

**NO-GO pending FTAI** under the strict 12/12 condition. FTAI Q2 2026 has
issuer IR HTML/PDF, SEC filing and issuer-distributed GlobeNewswire
statement, but current Actions downloads still fail with HTTP 403. The
[controlled original-PDF import fallback](MANUAL_OFFICIAL_REPORT_IMPORT.md)
requires a real official PDF, SHA from that PDF's bytes, and human-review
confirmation before safely importing original statement rows. A URL, mirrored
copy, manual transcription or a passed fixture alone is **not** successful
official-content intake. Do not merge unless the owner expressly changes the
release gate or original FTAI document extraction succeeds.

### 2026-10-26 financial-intelligence gate audit

PR #60 now tests an additional official **SEC Company Facts JSON** intake route for
FTAI Aviation CIK **1590364**, Q2 2026 10-Q accession
`0001628280-26-051412`. The adapter requires exact SEC CIK/name, filing date,
3-month fiscal dates, `10-Q` form, US-GAAP tags and same-accession
comparatives. It computes SHA-256 over the **actual HTTP response bytes** and
never turns H1 totals into Q2. The JSON digest is **not** a PDF digest.
The official endpoint's inclusion in the allowlist or passing mocked-source
tests does **not** prove the GitHub runner fetched the feed. See the current
PR source-intake artifact before changing release status. As of the last
attested 11/12 run, FTAI did not have retained financial observations.

For SMCI, source-backed **cash, inventory and accounts receivable** are now
independently scoped **balance-sheet instants** at FY2026/FY2025 year end.
They are not operating cash flows, cash expenses or new forecast assumptions.
Deterministic Hebrew comparisons derive gross/operating profit margin changes
only if current and historical revenue and profit share the same original
source version, currency and identical duration columns. These are
review-only descriptions, not beats/misses or automatic scenario revisions.

The collector prefers a newer fiscal quarter over older curated document
pointers, without claiming that a scheduled future earnings announcement is a
published filing. Per-company metric/status counts are logged in the read-only
CI source audit. The existing 12-company AI packets carry Hebrew findings and
questions as **unapproved input**, not output from a paid model.

FTAI's October 6 official release schedules Q3 2026 results for
**October 29, 2026**. On October 26, Q2 remains the last verified published
quarterly report. This date is for the next operator check, not proof that
a Q3 result already exists.

The model comparison identifies mismatched accounting periods/bases instead
of calculating spurious surprise percentages. Primary supplied DLO valuation
remains separate from the older JSON model. No live prices, buy/sell signals,
automatic target/probability updates or autonomous AI analysis are implied.

All personal research and portfolio edits remain in **browser local storage**.
This is not encrypted, shared, or synchronized across devices. Export backups
before clearing browser data, uninstalling or migrating devices.

## Persistence and publication contract

The existing `Publish PULSE` workflow is the only production data pipeline:

1. On an authorized push to `main` or scheduled/manual run, the `collect`
   job checks out `main` and seeds the prior approved public state from
   `pulse-data`. Failure to fetch that branch is intentionally fatal.
2. It collects issuer evidence, validates provisional financial observations,
   generates `issuer-coverage.json` for all twelve issuers,
   `latest-research-updates.json`, then uses
   `research_update_history.py` to append unique **content IDs** to the
   bounded `research-update-history.json` archive. Repeated polling does not
   fabricate a new event; only verified *source-bounded review-only* records
   with metrics enter the public archive. At most 12 versions per company are
   retained, so this is a limited operational history, not permanent backup.
3. Tests/build execute against the same in-memory public snapshot.
4. The `persist` job refuses to write if the prior `pulse-data` commit SHA
   differs from the one fetched by `collect`. Only the enumerated public
   data JSON files are copied and committed. It never edits personal research,
   PDFs or valuation source files.
5. The `deploy` job refuses superseded `main` and `pulse-data` hashes,
   then publishes the built artifact to GitHub Pages.
6. Production browser verification runs after the manual/code-triggered
   deployment. Scheduled runs omit browser verification to limit runtime.

`generatedAt` identifies snapshot generation, **not** a new issuer
publication. Use each report's `publishedDate` to judge its age and
`firstSeenAt` in the history for the first archived version. An unavailable
source must not be described as a successful fresh data update.

## Release gate before the owner's approval

- [ ] Latest PR head has successful Python, JS/Vitest, TypeScript/production
  build, real official source retrieval and mobile Chromium checks.
- [ ] Inspect `issuer-coverage.json` for all 12 companies, compare its
  retained-document count against original issuer intake, verify DLO/IREN and
  BWAY/SMCI source rows, fiscal dates, currency units, SHA, and review statuses.
  Do not mislabel a successful source index scan as a successful report fetch.
- [ ] Compare all retained PDF SHA-256 values with the supplied manifest.
- [ ] Verify no new secret, API key, personal holdings, automatic valuation
  mutation or paid model call appears in the changed files.
- [ ] Preview 320/390/430px RTL, 200% text and PDF viewing; capture
  screenshots and JSON/CI links in PR #60.
- [ ] Confirm `main` remains untouched and PR is still unmerged.

A passing branch CI is **not** proof of GitHub Pages deployment or a physical
Android installation. If any gate fails, continue work on PR #60.

## After an explicit authorization to merge (not before)

1. Check the PR head and protected branch again. Merge only after approval.
2. In GitHub Settings → Pages confirm deployment source is **GitHub Actions**.
3. Use Actions → **Publish PULSE** → Run workflow on **main**. Paid AI does
   not execute from this workflow.
4. Verify `collect`, `persist`, and `deploy` conclusions separately.
5. Inspect the `pulse-data` commit and confirm
   `public/data/research-update-history.json`, the latest snapshot and
   older financial datasets persist without unrelated changes.
6. Open `https://roeeazaria55.github.io/pulse-investment-research./` from
   an actual Android Chrome browser. Compare rendered DLO/IREN values with
   the newly deployed `/pulse-investment-research./data/*.json`.
7. Confirm PWA installation, close/reopen, refresh, PDF navigation, personal
   research edit/save/reopen, airplane-mode *cached* research and a clear
   offline warning. A Playwright emulation does not replace this check.
8. Inspect one subsequent scheduled run for deduplicated history. Until it
   actually occurs, do not claim scheduled end-to-end collection is verified.

### Rollback without destroying research

If the new deployment fails, record the failed run ID, deployed `main`
commit, `pulse-data` commit and screenshots. With separate owner approval,
revert the release commit on `main` and redeploy the previous known-good
application shell. Do **not** reset, force-push, delete or roll back
`pulse-data` merely to revert UI code: doing so may destroy newer
source-backed research history. Preserve all public data artifacts and
personal browser exports. If an old shell cannot interpret a newer public
snapshot, first display an honest unavailable state rather than replacing
source data with invented defaults.

## AI v1.1 — private review, not part of v1 launch

The public GitHub Actions **Analyst packet preflight** is free/read-only.
There is intentionally **no paid AI call inside public Actions**: artifacts
and logs in a public repository are not a private review channel.

For a later authorized private-machine pilot only:

- Install prerequisites and obtain source-backed PULSE evidence locally.
- Create a dedicated OpenAI API key and enforce billing/usage limits. ChatGPT
  Plus does not include API usage.
- Set `OPENAI_API_KEY` and `PULSE_PAID_AI_APPROVED=YES` as environment
  variables on that **private machine**, not in repository content.
- Run, for example, from the repository root:
  `python3 scripts/run_optional_ai_review.py --ticker DLO --execute --private-output /home/user/private-reviews/dlo-review.json`
  (use an existing private directory **outside the repository**, a unique
  absolute .json path and local OS permissions).
- The runner validates the packet, requires a completed model API response,
  checks exact cited evidence IDs and output structure, writes a 0600 file,
  and reports only counts/hashes. This path has **not** been exercised with
  a live paid call. Suggested scenario probabilities are reviewer proposals,
  not updated targets or portfolio actions.

The local JSON is for human review. A private, controlled import/review and
approval UX is a **separate v1.1 task**; until delivered and verified, AI
must not silently update public research or valuations.
