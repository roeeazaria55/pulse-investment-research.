# PULSE — release gate for research intake and thesis comparison

Date: 2026-10-21. Status: **NOT APPROVED FOR MERGE** until all required gates are checked on the final merged branch.

## Scope of this release
- Read-only Phase 0 provenance and status for 12 companies.
- Seven **unverified** scenario candidate records; not approved recommendations or live prices.
- Source-mapped report vs thesis comparison summary on the existing monitor.
- Explicit review flags and source evidence; no automatic valuation promotion, portfolio changes, or trades.

## Required, ordered gates
1. **Sync the feature branch** `pulse/phase0-research-audit-20261021` with the latest `main` via a real conflict-aware Git merge (or GitHub "Update branch"). At the time of this checklist the branch is 3 commits behind and 45 ahead. Inspect every conflict. Do not force-update or discard the commits on main.
2. **Verify release scope** in PR #21 against the merged diff. The seven new PDF binaries and seven page-JSON sources have **not** been committed. Source manifest's `external_import_bundle_only` claim must remain accurate. The import backlog cannot be presented as finished.
3. **Research consistency review**: check company identities (Gilat Telecom ≠ Gilat Satellite Networks), date / valuation horizon / fiscal period / USD-ILS-agorot units; source-vs-model distinctions; scenario probabilities; and reference vs live price labels.
4. **Known review items**: FTAI declared weighted price differs from recomputed values; Next Vision corrected H1 historicals have not yet recalibrated future forecasts; NBIS and IREN funding/dilution bridges; ENLT debt double counting; Gilat Telecom diluted shares/lease treatment. Show unresolved items as pending; do not silently promote.
5. **Public data/privacy review**: confirm no private portfolio, watchlist overrides, decision journal, access tokens or unpublished licensed material leaks into `public/` or the build. PDF distribution needs explicit authorization and verified hashes before import.
6. **Functional QA**: new summary appears on supported research monitors; zero matches are presented as missing, not zero actuals; conflicts/revisions block numerical surprises; historical observations never compare to a different forecast period; all source links and RTL/mobile layouts work.
7. **CI on the synced head**: Python unit tests, official-source metadata/content read-only checks, `npm test`, `npm run build`, mobile/browser/PDF worker/persistence checks all green. Previous CI #75 passed on the **pre-sync** commit `cb1b513`, and does not substitute for this final run.
8. **Merge and post-deploy smoke**: only after reviewer sign-off and green synced CI merge PR #21 to `main`, verify GitHub Pages deployment and test site on desktop and phone, including portfolio local persistence and unverified source labels. Keep a known-good commit for rollback.

## Explicitly out of release scope
- Importing seven original PDFs and page JSON files without original bytes and distributable permissions.
- Full automated mapping of all 12 issuers; company-specific mappings require separate source-verified tests.
- Automatic live target price changes, investment recommendations, personal portfolio publication, or trading.
- Claims that 12 sources or all financial results are independently verified.

## Evidence
- PR: https://github.com/roeeazaria55/pulse-investment-research./pull/21
- Last fully green pre-sync CI: https://github.com/roeeazaria55/pulse-investment-research./actions/runs/39584607614
