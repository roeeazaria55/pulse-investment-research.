# PULSE — Remaining Work & Production Acceptance Plan
Date: 2026-10-28
Baseline: PR #60, unified financial intelligence (12 issuers / 66 retained source-bound metrics).
Status: forward-looking engineering instructions, NOT a claim these tasks have been completed.

## Mission for the next Codex sprint
Finish the outstanding work after the tested unified feature set is merged, without changing approved portfolio positions, PDFs, analyst targets, Bear/Base/Bull scenario probabilities, or published user research without explicit approval. Prefer existing React + Vite + GitHub Pages + GitHub Actions + pulse-data architecture. No paid APIs, new backend, force-push, or silent release.

Create a fresh feature branch from the ACTUAL current main HEAD and a new PR. Do not reuse the already-merged PR #60. Start by inspecting the live release's workflow status and the previous [implementation report](PULSE_UNIFIED_BUILD_REPORT.md). Use independent, reviewable commits for each deliverable. Run the full test matrix before recommending another release.

## P0 — Production verification and rollback gate
1. Inspect the main commit, Pages deployment workflow, artifact contents and publication outcome. Distinguish a completed build from successful persistence to pulse-data and from a functioning deployed website.
2. Validate browser navigation and 320/390/430px RTL layouts, 200% text, the five screens, PDF/worker loading, Service Worker update, offline last-good research, and local portfolio/read-state preservation.
3. Test deployed paths and deep links under the exact repository-name URL. Use a real Android device for installation/offline/notification claims; otherwise mark these as UNVERIFIED and supply a device checklist.
4. Verify non-destructive data persistence: no overwrite of protected portfolio, source-linked research history or prior pulse-data snapshots. Capture baseline and new IDs/SHA hashes; record rollback to the prior main commit if a regression is observed.
5. Do not infer delivery of Push from an HTTP success. No user secret is allowed in browser code or logs.

Acceptance: GitHub Pages workflow passes, deployed content version matches main, pulse-data persistence is checked, and a manual go/no-go checklist lists every unverified real-device check. If a fatal regression appears, stop and propose a reversible rollback; do not claim it is healthy.

## P1 — Financial source verification and reconciliation
1. For each of the 12 issuers, build a source-by-source coverage matrix: newest verified issuer report, fiscal/calendar period start/end, publication date, units/currency, GAAP/IFRS/Non-GAAP/KPI label, raw evidence/digest, comparison eligibility, and analyst review status.
2. DLO (highest priority): reconcile the gross-profit driver and source definitions against the retained model and official Q2 2026 disclosures. Do not create a prior-period comparison or take-rate figure until definitions and proof match. If impossible, keep needs-reconciliation.
3. FTAI: verify next official release when actually published; do not infer Q3 from its scheduled 2026-10-29 event. Verify SEC accession and differentiate Q2 income statement vs H1 cash flow vs as-of balance values. Do not silently extend the Q2-bound SEC adapter.
4. NextVision: investigate 2026 official reports; don't mistake FY2025 for the latest 2026. Record source identity or failed-access reasons.
5. IREN: distinguish FY2026 historical baseline, new quarterly releases, AI revenue, customer advances, capex/capacity and financing needs. Prefer original issuer/SEC provenance.
6. Other issuers: map debt, cash, cash flow, segment information, capex, backlog or capacity *only* when actual accounting/operating definitions are supported. Retain pending-review, unmapped and unknown statuses as applicable. No false "12/12 newest reports" claim.
7. CI audit should output an artifact with source URLs, dates, number of fully comparable metrics, missing fields and unresolved discrepancies. Do not turn a technical parser check into analyst approval.

Acceptance: every company has transparent coverage; every new numerical metric is attributable and period-safe; DLO is either reconciled with evidence or clearly blocked. Source failures never erase good last-known observations.

## P2 — Real forecast and thesis decision support
1. Reuse the forecast archive and formally gated Actual-vs-Forecast comparison. A Beat/Meet/Miss may appear only if forecast was archived before publication, period/unit/basis exactly match, source is validated, and an enforced analyst-approval mechanism authorizes the fact.
2. Build bounded candidate interpretations for DLO, IREN and META as end-to-end examples. Separate FACT, DERIVED CALCULATION, HYPOTHESIS and ANALYST-APPROVED CONCLUSION.
3. For every potential thesis/valuation consequence, display the assumption affected, evidence, contrary interpretation, missing information, event date and review state; never auto-commit target prices.
4. Scenario recommendations must use per-company Bear/Base/Bull assumptions with evidence-based dynamic weights, individually explained, totaling 100%. They remain immutable draft candidates until explicitly approved. Never apply a fixed split or fabricate price targets.
5. Do not calculate "growth %" from a zero/negative baseline; report signed absolute change, and percentage-point change for ratio metrics.
6. Add regression tests proving refusal on stale revisions, post-publication forecasts, mixed periods, conflicting source data and unapproved judgments.

Acceptance: the three company examples are reproducible from provenance and cannot mutate official model data before approval.

## P3 — Autonomous scans and alert readiness
1. Reuse the current Collect → Extract → Validate → Compare → Research → Persist → Publish workflow rather than creating another scheduler. Confirm that Jerusalem 08:00 and 19:00 briefing boundaries remain correct across DST, failed jobs and delayed GitHub Actions runs.
2. Live-run or inspect official source checks under rate limits; validate external metadata, time zones, deduplication by event/source digest, relative materiality, and stable history. A headline cannot prove an issuer's financial result or cause a Critical alert.
3. News page should support all/unread, company and importance filters without losing local user state. Verify grouping of syndicated stories and distinction between article metadata and read issuer documents.
4. If Android Push is pursued, require explicit opt-in, authorized infrastructure, secure notification topic handling, a real device receipt test and documented opt-out. Until then display in-app alerts as the supported capability.
5. Run full pipeline with retained real issuer snapshots and controlled fault injection (404/403/timeout, duplicate filings, changed report layout, damaged snapshot, DST transitions). Never equate a simulated run with proven production execution.

Acceptance: source-to-news-to-research links work with evidence, failures are observable/non-destructive, and claims are scoped to actual tested conditions.

## Required checks and reporting
- Run npm ci; npm test; npm run typecheck; npm run build; npm run validate:data; python3 -m unittest discover -s scripts -p 'test_*.py'; PR Playwright mobile/offline/PDF checks.
- Preserve existing tests and public-vs-private access boundaries. Use only free providers and no paid LLM automation.
- Report test counts, run URLs, failure logs, deployment status, produced artifacts, affected files, source coverage, unresolved blockers and rollback instructions.
- Keep financial approval, mergers and release decisions explicit. Do not mark production acceptance "GO" unless the evidence supports it.
- Deliver code + tests + documentation in the next PR; not just a planning document.

## Ready-to-paste execution instruction
Implement P0–P3 in one coordinated Codex sprint on a NEW branch based on current main after PR #60 is merged. Prioritize user data protection, financial provenance, DST correctness and safe fail-closed behavior. Commit and push working code with tests; do not silently change research valuations, scenario weights or holdings; do not merge the next PR or deploy unreviewed changes without explicit owner approval. If any dependency fails, document the limitation and continue safe independent work.
