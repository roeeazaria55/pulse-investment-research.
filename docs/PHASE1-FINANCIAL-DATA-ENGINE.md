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

## NBIS / IREN / DLO evidence audit (21 October 2026)

Reviewed the structured report snapshot at commit `c9c82cd6a0d65679f20f67422902d5d8f5d9de89`,
the intake parser, mappings, comparison gates and company research/model records.
NBIS has four read documents and DLO three; each has **zero structured facts**.
Their extracted table rows require a source-specific adapter that verifies headers,
units, periods and consolidation scope. DLO's last collection failed with HTTP 403;
older successful reads remain evidence of those documents, not complete coverage.
IREN has research and valuation records, but no entry in report intake and is not
in `scripts/report_intake.py`'s current pilot set. Narrative source links and model
capital values are not automatically mappable structured report facts.

No new accounting mappings are enabled by this audit. SMCI/BWAY mappings remain
unchanged. `financialMappingReadiness.ts` exposes source availability, raw structured
fact counts, document revision/failure flags and company-specific review requirements.
The intake panel now displays these gaps for all three pilots, including IREN when
there is no intake entry. Unsupported forecast comparisons explain the evidence gap
and return no observation or numeric difference, even if unreviewed/conflicting
facts appear in a later snapshot. Tests distinguish unknown availability, missing
reports, table-only evidence, raw facts without a mapping, revisions and failures.

Next safe step: implement and fixture-test a source-specific adapter for one official
report, retaining issuer identity, consolidation scope, exact dates, units, accounting
basis and source provenance. IREN intake configuration is corrected below.
Only then can reviewed mappings be added; fiscal-June and calendar periods, adjusted
EBITDA and operating profit, ARR and recognized revenue, corporate and merchant cash,
and weighted-average diluted shares versus model dilution must stay distinct.

## IREN intake follow-up

Root causes: `candidate-iren` was excluded from the content collector pilot set,
and the financial-title filter did not recognize the official FY26 annual-results
title already present in metadata. The registry itself was not missing. Existing
IR discovery attempts had HTTP 403 errors, but the verified issuer-distributed
GlobeNewswire source had retained the actual annual-results release:
https://rss.globenewswire.com/news-release/2026/08/27/3352401/0/en/iren-reports-fy26-results.html

The collector now includes IREN, recognizes FY26/FY2026 labels for discovery and
ranking only, and preserves explicit unknown publication status when no report
record exists. Failed discovery without candidates is recorded as a failure;
failed report reads retain previous successful evidence. Python fixtures cover
selection, ordering, schedules, issuer/path restrictions, missing records, network
failure, retained history and budget deferral. UI tests distinguish missing entries,
recorded failures and no matching records. These fixtures contain no issuer figures.

The local live attempt was blocked by an unavailable proxy. Its intake source status
is recorded as failed, not as an absent/unpublished report. The PR CI performs an
independent live attempt and preserves its generated snapshot as an evidence artifact.
No IREN financial metric mapping or active research target is enabled by this change.

## Phase 1B — checked IREN and SMCI baseline cards

`financialResults.ts` now owns strict cell parsing, source identity/header/unit checks,
duplicate/conflict handling, explicit transformations, provenance and dated comparison
gates. Issuer modules supply bounded statement rules; `FinancialResults.tsx` renders
both companies in RTL. These are saved checked extracts, not live reads, original-file
archives or analyst-approved observations. Missing/mismatched source cells fail closed.

IREN's original source extract and research/model files are unchanged: FY2026 revenue
707.0, operating cash flow 2,100.4 and selected derived CAPEX 4,333.1, all USD million.
CAPEX remains the negative sum of the two identified cash-payment rows.

SMCI uses the official consolidated FY2026 10-K, year 2025-07-01 to 2026-06-30,
[filed 2026-08-31](https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/0001375365-26-000022-index.html).
[Statement pages 59 and 63](https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm)
report net sales 39,063,072, operating income 2,770,486 and operating cash flow
(6,809,886), in USD thousands. The shared adapter explicitly divides by 1,000
to display 39,063.072, 2,770.486 and -6,809.886 USD million. These are US GAAP
consolidated measures, not adjusted earnings, EBITDA, orders or FCF. The bounded
extract retains raw cells, location, filing date and the earlier intake version's
hash/context; it does not claim to archive the source bytes.

SMCI first announced the results on [2026-08-11](https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Financial-Results/default.aspx).
The comparison gate uses that earlier date rather than the later 10-K filing date.
Existing PULSE revenue assumptions are FY2027 in USD billion; there are no matching
numeric FY2026 operating-income or CFO targets. No FY2026 surprise is calculated.
IREN's later research and future FY2027 assumptions are likewise preserved.
The existing intake-driven thesis monitor and its summary also reject unknown,
same-day and post-publication forecast timing before computing any numeric gap.

Regression coverage includes both issuers, wrong company/source/period/unit/page,
unavailable sources, revisions, duplicates/conflicts, missing metrics, signed CFO,
derived CAPEX and the publication-order gate. The PR workflow runs JavaScript,
Python, production build and mobile checks at 320/390/430 pixels with 200% text,
including both financial cards and the existing research/PDF regression checks.

