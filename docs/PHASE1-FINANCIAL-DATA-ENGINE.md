# PULSE Phase 1 — Financial data engine

## Goal
Make issuer-source-to-forecast comparisons dependable before introducing AI-based investment conclusions.

## Baseline
- Twelve company research records exist; full-text user analyses are **not verified issuer filings**.
- Structured issuer facts currently have explicit mappings for two SMCI metrics and two BrainsWay metrics only. Coverage does not mean those facts were actually ingested.
- Existing thesis comparison enforces exact period, unit and accounting definition matching; corrected/stale/conflicting reports are review-only.
- `src/research/financialDataCoverage.ts` provides a machine-readable coverage backlog, not an assertion of available or verified source data.

## Pilot acceptance gates (SMCI, BrainsWay, NBIS, IREN, then DLO)
1. Discover issuer statements on allowlisted official domains; preserve exact original URL, SHA-256, context, unit, period, filing timestamp, and revision provenance.
2. Add semantic mappings only after checking concept, consolidation scope, fiscal calendar, duration vs instantaneous context, and company-specific accounting basis.
3. For cash flow, reject quarter/YTD mismatches; do not infer quarterly flow by subtracting YTD amounts without a reviewed transformation and source context.
4. Do not map ARR, contract backlog, adjusted earnings or management projections into GAAP revenue, net income or free cash flow.
5. Add positive, conflicting-fact, revised-report, restatement, unit/currency and wrong-period tests for each new mapping.
6. UI must show source evidence and mark numeric gaps provisional until analyst verification; no automatic target-price or probability promotion.
7. Re-run CI, production build and browser/mobile tests before a feature PR is merged.

## Next implementation slice
- Extract the existing semantic mapping registry into its own typed module and use it from both report comparison and the coverage summary.
- Introduce explicit per-company mappings for NBIS, IREN and DLO **only when filing evidence supports exact matching**.
- Persist an auditable history of verified report observations separately from personal portfolio data.
- Add source-cited post-earnings comparison cards and an analyst-approval change log.

This plan does not promise unattended background execution or unattended trading.
