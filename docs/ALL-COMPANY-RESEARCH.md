# Dated research baselines for all eleven companies

## Scope

All 11 registry identities have one readable baseline and the existing eleven
research fields, source URLs, missing-input list, report period and preparation
date. The ten new baselines are sourced from company filings, issuer releases or
company-distributed releases; NBIS retains its previously published baseline.
These are ChatGPT-authored static research, not an automated model or complete
current investment recommendations. No price targets are fabricated. Scenarios
are qualitative and explicitly distinct from reported facts/management targets.

## Review notes

- NextVision: company-distributed Q2 release governs the figures. The August
  presentation's page 19 column labels conflict with the release/other slides.
  Baseline discloses that discrepancy and does not copy the mismatched table.
- META: revenue vs margin pressure and capital expenditure/cash conversion.
- DLO: TPV vs revenue vs gross profit; corporate vs merchant funds.
- FTAI: segment vs consolidated results; EBITDA vs unavailable FCF bridge.
- LMND: IFP vs recognized revenue; insurance losses/adjustments vs GAAP profit.
- SNDK: fiscal period, cyclical pricing and adjusted cash flows after NBM funding.
- IREN: contracted/operating ARR vs recognized AI revenue; GPU financing vs FCF.
- Enlight: revenue and tax-benefit income, asset sale gains and interest cash-flow
  reclassification. Inaccessible October deck is explicitly excluded.
- BrainsWay: RPO vs revenue, restricted cash, insurer coverage vs actual usage.
- Gilat Telecom: identity distinct from Gilat Satellite Networks, ILS thousands
  converted to millions, consolidated vs parent cash flow, financing vs operations.

Each dataset contains the primary URLs and explicit source limitations. Source
metadata checks and schema validation do not independently verify financial facts.
No personal notes, portfolio allocations or existing local research are uploaded.

## Reading and adoption

Rendering or comparing a baseline does not write personal data. Applying selected
fields uses the existing draft/save workflow and retains notes plus up to three
previous versions. Per-company IDs prevent cross-company adoption. The eleven
baselines are independent and may be reverted separately from the UI change.

## Updates requiring review

The status card fetches the same validated official snapshot as the source panel.
Uncited URLs for the selected company are listed for review; this does not mean
that they are all new or financially material. Dates after the research date are
labeled later, earlier dates are labeled prior information, and unknown dates
remain unknown. Query parameters do not create duplicate sources. Collection time
is never used as publication time. Failed fetch/validation displays unavailable
status while keeping baseline readable. A baseline older than 90 days gets a
review reminder, not a claim that younger research is complete/current.

## Validation and rollback

Unit/UI tests cover all eleven identities, full exchange validation, read-only
render/preview, personal-note retention, restorable versions, valid stored state,
uncited/unknown-date/duplicate sources and fetch failure. Mobile CI opens each of
the eleven full baselines at 320/390/430px and 200% font size before the existing
PDF/import/save/reload/restore flow. Headless emulation is not a physical phone.

Revert the per-company dataset commits and/or the integration commit. Removing a
published baseline does not undo a user's earlier explicit local adoption; local
research version history remains the recovery route. No collector, scheduling,
notification, API service or paid-data behavior changes in this work.

## Mobile follow-up

The first CI pass found DLO horizontal overflow at 320px with 200% font size.
Published baseline prose now permits wrapping inside nested cards; select width
is bounded without clipping content. The mobile test retains the assertion and
reports overflowing elements/saves a screenshot if a later regression occurs.
The overflow diagnostic identified the fixed bottom navigation, not the research
prose, on the repeated 200% company-switch check. Its five columns now have
explicit zero-minimum grid tracks and a viewport-bounded width; text can wrap.
The full repeated-company assertions remain enabled.
