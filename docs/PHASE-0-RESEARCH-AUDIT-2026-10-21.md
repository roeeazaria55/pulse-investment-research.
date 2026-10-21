# PULSE — Phase 0: research intake audit (21 October 2026)

**Status: intake/audit only; NOT a verified financial dataset, approved valuation, or live quotation.**

## Scope and precedence

The user's 12-company coverage set is NBIS, SNDK, DLO, LMND, META, FTAI, IREN, Next Vision, ENLT, BrainsWay, SMCI and **Gilat Telecom** (not Gilat Satellite Networks). This matches the 12-identity official registry. Existing baseline JSON, calculations, private notes and portfolio state must not be overwritten by an intake operation.

- Keep original PDFs byte-for-byte with SHA-256 when they are actually imported. Never claim ingestion of a PDF that has not been copied and hash-verified.
- Prefer **PULSE_META_Full_Research_HE_FIXED.pdf** and **PULSE_NextVision_Full_Research_HE_FIXED.pdf** over their earlier PDFs missing numeric table values.
- For each company preserve: complete source analysis, numerical tables, as-of date, source references, model formula and inputs, financial reporting period, *valuation horizon*, currency, Bear/Base/Bull probabilities **and the company-specific justification**, monitoring thesis, explicit unknowns, and version history.
- Distinguish source-authored claims, primary-source-confirmed facts, management guidance, analyst assumptions, and mechanically calculated numbers. No assertion of primary-source verification is implied by PDF receipt.
- When the latest PDF conflicts with the application's existing baseline, create a **candidate update**, show both versions and highlight changes; never silently switch the live research.
- Some sources refer to late-2027 valuations using 2028 earnings; do not imply those are 12-month targets or discount twice. Separate end-date valuation and present value.
- Do not promote private personal portfolio, watchlist overrides or decision notes into a public repository or Pages JSON.

## Research intake register

| Company | Latest user-supplied research name | Primary company-specific follow-up | Status |
|---|---|---|---|
| NBIS | PULSE_NBIS_Full_Research_HE.pdf | GPU economics, capex, funding, dilution and conversion of capacity to recognized revenue | Source PDF previously incorporated in repo; re-audit |
| SNDK | PULSE_SNDK_Full_Research_HE.pdf | NAND pricing, normalized margin, capital needs and FY2028-to-horizon bridge | Source PDF previously incorporated in repo; re-audit |
| DLO | PULSE_DLO_Full_Research_HE.pdf | TPV/gross profit, corporate versus merchant cash, true FCF | Source PDF previously incorporated in repo; re-audit |
| BrainsWay | PULSE_BWAY_Full_Research_HE.pdf | Treatment utilization, recognized revenue, regulatory reimbursement, diluted ADS/share unit | Source PDF previously incorporated in repo; re-audit |
| SMCI | PULSE_SMCI_Full_Research_HE.pdf | Cash conversion, working capital, margins and governance/accounting risks | Source PDF previously incorporated in repo; re-audit |
| LMND | PULSE_LMND_Full_Research_HE.pdf | Underwriting quality, current-year vs prior-year reserve movements, ADR, reinsurance, diluted shares | Newly supplied; source verification pending |
| META | PULSE_META_Full_Research_HE_FIXED.pdf | AI capex + finance leases, FCF, advertising economics and Reality Labs; avoid double counting | Newly supplied corrected PDF; source verification pending |
| FTAI | PULSE_FTAI_Full_Research_HE.pdf | Aerospace/Leasing/Power SOTP, segment-versus-group EBITDA, inventory, asset disposal and cash | Newly supplied; reconciliation needed |
| IREN | PULSE_IREN_Full_Research_HE_PreQ1FY27.pdf | Contracted ARR vs realized AI cloud revenue, capex, advances, GPU replacement and share dilution | Newly supplied; source verification pending |
| Next Vision | PULSE_NextVision_Full_Research_HE_FIXED.pdf | Order backlog, recognized sales, margins, normalized income and dilution; rebase after corrected H1 | Newly supplied corrected PDF; recalibration needed |
| ENLT | PULSE_ENLT_Full_Research_HE_PreQ3.pdf | Project COD, tax equity, project debt, cash available for distribution, avoid net-debt double counting | Newly supplied; source verification pending |
| Gilat Telecom | PULSE_Gilat_Telecom_Full_Research_HE.pdf | Lease-adjusted FCF, convertible debentures, fully diluted shares, NIS agorot pricing | Newly supplied; source verification pending |

**Important:** This register records documents seen in the conversation or previously documented as incorporated in GitHub. It is not a declaration that the newly supplied PDF bytes are in GitHub.

## Immediate arithmetic / model reconciliation queue

| Priority | Company | Finding | Required action |
|---|---|---|---|
| P0 | FTAI | Displayed scenario values $75.5/$174.4/$269.1 and 30/50/20 weights imply **$163.67**, not the source's ~$164.1. | Reproduce SOTP from unrounded inputs, inspect net debt/claims and compare rounded-vs-precise weighted target; do not silently overwrite source figure. |
| P0 | Next Vision | Corrected H1 2026 revenue $144.9M / net income $80.8M replace earlier incorrect $155.5M / $91.9M, but projected normalized earnings were **not recalibrated**. | Keep original forecasts flagged as provisional; verify source H1 and rebuild the earnings bridge before target approval. |
| P0 | NBIS / IREN | Both require explicit cash/debt/dilution and hardware refresh bridges; contracted power, ARR, cash advances and GAAP revenue are distinct concepts. | Build source-anchored period-matched funding bridges before valuing on a per-share basis. |
| P0 | ENLT | Project EV, project equity NAV and consolidated debt may overlap; cash available for distribution is not consolidated EBITDA. | Set valuation basis per project and test against debt double counts. |
| P0 | Gilat Telecom | 125M diluted shares in base case are an assumption, not a verified current figure; lease treatment changes net cash and FCF. | Validate conversions, treasury stock, lease principal payments, and agorot/share unit before acceptance. |
| P1 | LMND | 29.88 × 30% + 60.24 × 45% + 113.58 × 25% = **$64.455** (rounds to $64.46). | Preserve source's temporary status; verify underwriting base and company filings before promoting target. |
| P1 | META | 459 × 30% + 847 × 50% + 1,208 × 20% = **$802.80**. | Verify Q2 facts and build consistent FCF accounting for capex/finance leases; 2027 ending value is not today's value. |
| P1 | IREN | 11.5 × 35% + 41.1 × 45% + 80.7 × 20% = **$38.66**, matching rounded $38.7. | Show precision separately from source's estimate; verify valuation horizon and financing claims. |
| P1 | Next Vision | 90.7 × 25% + 215.8 × 55% + 340.3 × 20% = **₪209.43**. | Historical reference ₪187.90 and FX assumption ₪3.10/$ must remain dated. |
| P1 | Gilat Telecom | 125 × 25% + 245 × 55% + 419 × 20% = **249.8 agorot**, rounded 250. | Keep all numerical units in agorot/share, not NIS/share. |
| P1 | ENLT | 46 × 30% + 78 × 50% + 118 × 20% = **$76.40**. | Preserve 2028 EBITDA/end-2027 horizon distinction. |

**No live market price verification or independent issuer-document verification has been carried out in this phase.** Prices above are historical references and source-based assumptions.

## Development order and gates

1. **Intake contract**: design source document registry + approved/unverified/rejected fact flags, immutable document version IDs, strict currency/unit/fiscal period typing, source URLs, model calculation provenance and separate research-vs-personal state. Candidate imports must be preview-only until explicit adoption.
2. **Model reproducibility**: create pure calculations/tests for all 12, including distinct SOTP, sales, earnings and capital bridges; capture discrepancies rather than mutating the primary research. No single hardcoded 20/50/30 probability across companies.
3. **Thesis-monitor expansion**: six measurable, source-based thesis drivers per company; start with existing NBIS/SNDK and report-intake five-company pilot; ensure no numeric comparison across periods/accounting definitions.
4. **Official report mapping**: add reviewed source-specific mappings and accounting bridges (not positional guessing from PDF tables); produce source-cited diffs and proposed research revisions, never auto-approve them.
5. **Decision and risk layer**: private decision journal, factor exposure/correlation caveats, portfolio stress tests, historical forecast scoring. Do not publish personal allocations in GitHub Pages.
6. **AI challenge / explanation**: only with reliable model, evidence citations, controlled server-side credentials and budget; distinguish supported findings from hypotheses.

### Phase 0 acceptance gate

- Every one of the 12 companies has an immutable original source reference; corrected superseding PDFs are chosen for META and Next Vision.
- Per-company validation confirms scenario weight sum=100%, recomputed values, price-unit/FX, periods, horizons and claims made about source verification.
- Any mismatches remain visible in an audit queue with a resolution and reviewer confirmation; do not publish a silently adjusted valuation.
- All current TypeScript, unit, browser RTL and production-build tests pass on the change branch; no change to public feed, active user research or live portfolio without explicit review.
- Only after these conditions are met should Phase 1 automatic thesis comparison be considered active.

## Codex instructions for next implementation PR

First inspect `src/data/suppliedResearch.json`, `src/data/models/`, `src/research/scenarioModel.ts`, `src/research/reportComparison.ts`, `src/components/ThesisMonitor.tsx`, `scripts/report_intake.py`, `schemas/`, and current tests. Propose a backward-compatible schema + preview/diff for corrected or new research; avoid duplicating the existing system. Begin with tests demonstrating FTAI discrepancy detection, corrected Next Vision supersession, strict horizons, and 100%-sum per-company weights. Do not auto-merge or auto-deploy until tests and source integrity are confirmed.
