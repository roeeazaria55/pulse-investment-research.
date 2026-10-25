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

All 12 companies in `public/data/official-registry.json` now have explicit
source-index/document-fetch/research states; this is **not** twelve companies
with verified financial extraction. Retained original issuer content currently
exists for NBIS, DLO, LMND, SNDK, IREN, Next Vision, BrainsWay and SMCI
in the latest branch CI snapshot. The numeric pilot is
DLO (reconciliation), IREN (curated historical FY2026), BrainsWay (strict
unaudited Q2-2026/Q2-2025 revenue + gross-profit statement cells) and SMCI
(typed annual SEC XBRL revenue, gross profit and operating cash flow).
All extracted rows still require analyst review. Missing filings, invalid
table layouts and HTTP 403 must remain explicitly shown, not filled with
guessed figures.

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
