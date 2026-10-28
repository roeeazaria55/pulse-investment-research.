# PULSE Unified Financial Intelligence — implementation and release review

**Date:** 2026-10-28  
**Branch:** `pulse/p0-working-research-engine-20261025`  
**Pull request:** #60 — review-only draft; no merge, main changes or production deployment.

## Implemented in this unified pass

### 1. Financial integrity
- `scripts/financial_integrity_audit.py`: independent read-only consistency check of the existing issuer registry and latest financial research snapshot; checks all expected issuers, source host matching, source digest presence, duplicate metrics, finite numbers, accounting dates, missing prior-period references and DLO reconciliation restrictions.
- Writes `work/financial-integrity-audit.json` (CI artifact), with the original technical/analyst status preserved. **A passing audit does not approve financial facts.**
- Python regression tests, and an additional PR CI stage before release checks.
- The earlier 12-company/66-metric coverage is a documented baseline only, not a fresh attestation that every issuer's newest report was acquired.
- DLO is still a *needs-reconciliation* case. FTAI Q2's SEC evidence was previously retained. No invented Q3 data, latest-filing claims or numerical reconciliation.

### 2. Mobile/readiness
- Integrated a collapsed, source-aware research alert inbox into the existing News view. It uses existing read IDs in local storage and existing source/event grouping, without a new storage schema.
- Added source-bound arithmetic questions to the existing Latest Research Update component under an expandable disclosure, preserving the research and valuation layouts.
- Existing local/CI mobile, RTL, PWA, PDF import and offline tests are retained. This pass does **not** claim physical Android testing, production Pages testing, or production `pulse-data` persistence proof.

### 3. Evidence-first research engine
- `src/research/evidenceInsights.ts`: deterministic, typed current/prior arithmetic restricted to comparable accounting periods and known metric meanings.
- Disallows comparisons if the prior period is missing or incompatible, refuses percentage-growth claims for negative/zero/sign-crossing baselines and treats percentages as percentage-point changes.
- Blocks DLO historical comparison while reconciliation is pending.
- Reports calculations and explicit analyst questions; **never** generates Beat/Miss, price targets, approved thesis changes or Bear/Base/Bull weights.
- Existing forecast comparison engine remains permission-gated; no retroactive forecast or analyst approval is fabricated.

### 4. Automated intelligence and alerts
- `scripts/build_intelligence.py`: two distinct Jerusalem-time briefing windows, ending at 08:00 and 19:00, with DST-aware UTC boundaries and stable window IDs.
- Existing ingestion workflow may poll more frequently. A completed brief can only be created on the first actual workflow run after the local boundary, not at a guaranteed second.
- `schemas/intelligence.schema.json` keeps legacy 13:00 records readable alongside new windows; `DailyPanel` labels morning/evening and links unique briefing IDs.
- `src/research/alertPolicy.ts` uses existing verified-source event scores and event groups. No headline-only source is promoted to a high or critical alert. Duplicate event groups and already-read alerts are excluded.
- Notification delivery to Android remains an **unverified optional capability**, not a claimed working Push system.

## Regression and safety boundaries
- Added unit coverage for period mismatches, missing source and date, invalid percentage comparisons, balance-sheet date comparisons, DLO unreconciled status, alert read state and event-group deduplication, as well as DST transitions.
- PR checks: `npm ci`, `python3 -m unittest discover -s scripts -p 'test_*.py'`, read-only issuer source scan/intake, Python integrity audit, `npm test`, `npm run typecheck`, `npm run validate:data`, `npm run build` and mobile Playwright. Check the **current PR head** for final pass/fail.
- No model/PDF/portfolio state was deliberately modified; no paid LLM, new backend, secret exposure, merge, force push, or deployment.

## Known gaps — do not silently mark complete
1. Analyst approval of the financial facts and DLO source reconciliation. Many company-specific debt, CAPEX, capacity, backlog and segment mappings remain unavailable.
2. The latest issuer filing was not independently verified for every company during this pass.
3. Actual-vs-forecast Beat/Miss remains blocked when forecast provenance or approval is missing. No dynamic scenario probabilities were generated without sufficiently trustworthy evidence.
4. No full new-report-to-news-to-validated-thesis roundtrip was proven in a deployed environment; available tests are simulated or CI read-only.
5. Physical Android PWA, live GitHub Pages offline behavior, live scheduled 08:00/19:00 execution, persistent production `pulse-data` and device Push delivery remain unverified.

## Release decision

**NO-GO for automatic merge/deployment or claiming finance-approved research.**
Eligible for code review when the head CI is green and the audit artifact is inspected. The maintainer should separately verify real Android and deployed PWA, confirm access controls and approve any future release.

## Operational note

The existing production Pages workflow polls roughly every 30 minutes (scheduled GitHub Actions can be delayed). This PR changes briefing *classification windows*, not production scheduling on `main` before an approved merge. Archive boundaries are computed in `Asia/Jerusalem` rather than by hardcoded UTC offsets.
