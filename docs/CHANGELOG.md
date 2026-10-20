# PULSE change log

Each numbered change below is kept in its own Git commit. The pull request lists
exact commit IDs and CI results. Revert an individual commit to undo that change;
revert the merged pull request to restore its preceding deployed code. Before
reverting, inspect any later changes that depend on the same code. Public source
snapshots update separately; personal browser holdings, notes and research are
not repository files and are never modified by these collector changes.

## Quality 1 — explicit document metadata

- Replaced generic ENG/HEB/View File labels with an issuer-page heading, nearby
  document heading, or a labeled filename fallback. Whitespace is normalized.
- Added source labels, language, title basis and document-period hints. A year in
  a path is never a publication date. A filename-derived period is marked as a
  hint requiring review.
- Publication dates require a distinct index time/date or explicit page
  publication metadata, with the source URL retained. Modified/event dates are
  not substituted. Adjacent cards cannot lend each other a publication date.
- Existing collected links keep IDs and first-collection timestamps. Failed
  sources retain prior records. Images/styles/scripts are rejected as documents.
- Added parser and provenance regression tests. PR checks collect live public
  metadata read-only before validating and building the exact test snapshot.
- Rollback: revert the commit named `Fix document labels and publication-date
  provenance`; retained earlier version-1 snapshots remain readable.

## Quality 2 — verified issuer distribution and Gilat coverage

- Added GlobeNewswire organization indexes for IREN, DLO, FTAI and BrainsWay.
  A matching publisher badge in the same card is required before collecting a
  release; unrelated publishers and law-firm mentions are rejected.
- Added Gilat Telecom's verified Satcom-Gilat investor financial/immediate
  reporting pages, including explicitly linked Maya reports. Dates must appear
  in an individual report entry; URL years are not used.
- Distributor releases are labeled separately from company-hosted IR documents.
  Registry additions do not imply successful collection; live CI reports actual
  availability, and blocked or empty sources remain visible.
- Validation: 51 Python tests, 60 JavaScript tests and production build passed.
- Rollback: revert `Add verified issuer distribution and Gilat investor sources`.
  The preceding metadata commit is `4129dd62d42f274c49f866d95efd35797627d43e`.

## Quality 3 — whole-answer import and recovery verification

- Import now accepts a complete ChatGPT answer containing exactly one fenced
  JSON object, while retaining company, date, field and source validation.
  Ambiguous multiple code blocks and malformed/truncated JSON are rejected.
- Preview and explicit field selection still precede any draft change.
- Added regression coverage for prior-version restoration, personal-note
  preservation and persistence compatibility. Extended mobile browser checks
  to save, reload, restore the previous thesis and retain the imported version.
- Validation: 62 JavaScript tests and production build passed locally; live
  source collection and full browser checks run in GitHub Actions.
- Rollback: revert `Accept single JSON answer blocks and verify research recovery`.
  Coverage commit: `63777de8375259bd8e952e9f09db5d505b34ad3f`.

## Night 1 — prevent menu documents from replacing financial reports

- Confirmed on 19 October 2026: all eight retained Gilat items were policy,
  accessibility and pay-equality menu links, not the financial/immediate reports
  present in the issuer pages. They exhausted the eight-link source limit.
- Exclude navigation/header/footer and menu-role links before applying that limit.
  A URL also linked in body content remains eligible. Remove an earlier menu-only
  record only after a successful source read proves that classification; failed
  sources still retain records. No publication date is inferred from a filename.
- Validation: 53 Python tests passed, including polluted-snapshot refresh,
  repeated body/menu links and blocked-source retention. Live collection and
  browser checks run on the PR; their results are recorded in its description.
- Rollback: revert `Exclude navigation documents before official source limits`.
  No personal browser data or main-branch snapshots are changed by this commit.

## Night 2 — meaningful report labels and Hebrew period hints

- Generic `Earning Release`, `Earnings Release` and `Investor Presentation`
  labels now include the containing heading or a clearly labeled company/file
  fallback, rather than hiding the identifiable document behind a generic title.
- Recognize explicit Hebrew quarter/annual periods and underscore-delimited
  filenames. Filename-derived periods remain `filename-hint`; path years, file
  dates and collection time never become publication dates. Opaque filenames
  remain unknown. Previously retained records update when seen again.
- Validation: 55 Python tests and 62 JavaScript tests passed; production build
  passed. Regression examples include actual NextVision filename forms.
- Rollback: revert `Clarify generic report titles and Hebrew period hints`.
  No personal notes, research or stored document contents are changed.

## Night 3 — section-only headings and source-scoped cleanup

- Follow-up inspection found NextVision links labeled Q1/Q2 under a heading
  containing only `Earning Release`. Treat such category-only headings as generic
  too, preserving a meaningful file fallback and its period provenance.
- Limit navigation cleanup to records collected by that same source, so a second
  index cannot remove a document legitimately linked in the first index's body.
- Validation: 57 Python tests passed, including both observed heading forms and
  a two-source shared-document fixture. JavaScript/UI code is unchanged.
- Rollback: revert `Handle generic section headings and scope navigation cleanup`.

## Coverage extension — 19 October 2026

- Add official homepage fallback indices for FTAI and SanDisk after live reads
  confirmed current release links there while news indices failed.
- Add Lemonade quarterly-results index and narrowly allow its official PDF
  upload path. Metadata only: PDF contents have not been read.
- Add Meta SEC submissions metadata with exact CIK/ticker identity validation,
  issuer-scoped archive paths, no redirects, bounded response and safe document
  names. Dates are filing dates, explicitly labeled in titles/source labels.
- BrainsWay investor homepage is reachable in a fresh live check; collection
  coverage remains subject to the final run and availability.
- Validation: 61 Python tests, 62 JavaScript tests and production build passed.
- Rollback: revert commit titled `Extend official coverage with issuer homepage
  fallbacks and validated Meta SEC filings`. Existing browser research untouched.
- GitHub upload blocked by automatic approval review; changes are local until
  permission is resolved. No merge or deployment performed.

- Live targeted collection: META 8, FTAI 3, LMND 8, SNDK 5, BrainsWay 3.
- Generic Shareholder letter / 10-Q report labels now use document context or
  filename; generic Release Details headings no longer replace issuer titles.
- Full live collection completed: 136 retained metadata records covering all
  11 companies (16 NBIS, 8 META, 16 DLO, 16 FTAI, 8 LMND, 10 SNDK,
  24 IREN, 15 NextVision, 1 Enlight, 11 BrainsWay, 11 Gilat Telecom).
  Four individual indices still fail; alternate sources cover their companies.
  Coverage is metadata presence, not complete document/financial analysis.

## 2026-10-19 — Cash/debt research bridges and NBIS numerical worksheet
- FTAI H1 cash flow and debt from SEC 10-Q; distinguish asset sales from
  recurring operations and carrying debt from issuance costs.
- Gilat consolidated cash bridge after capex, lease principal and interest;
  separate bonds, leases and restricted cash with explicit reporting date.
- NextVision period discrepancy resolved for the research against the issuer's
  Hebrew Q2 report; customer concentration quantified. Presentation correction
  remains unverified.
- NBIS editable illustrative end-2027 EV/revenue scenarios with diluted shares,
  debt/cash bridge, discounting, zero floor, input validation and reset.
  Seeds are examples, not a completed fair-value opinion; edits are temporary.
- See RESEARCH-VALUATION.md for provenance, limitations, tests and rollback.

## 2026-10-19 — NBIS sourced funding/dilution valuation
- Replace example cash/debt/share seeds with dated primary evidence, a full
  June-2026 → end-2027 conditional cash/funding bridge, eight note series,
  pre-funded warrants, awards and explicit assumed equity financing.
- Derive value from analyst revenue/margin/EBITDA multiple cases, show economic
  conversion without double-counting the retired debt, discounting and multiple
  required to justify the historical October 16 reference (not a live quote).
- Explicitly disclose conservative future maturity claims, the June-series
  reporting discrepancy, unverified current balances, funding availability,
  temporary edits, excluded private-asset value and legal-conversion limitations.
- Lazy-render the model only when opened. See NBIS-VALUATION.md for reproducible
  assumptions, preset outputs, validation requirements and rollback.

## 2026-10-19 — Restore user's original NBIS 12-month model
- Replace the active end-2027 model with recovered October 15 conversation
  targets 115/235/360, probabilities 20/50/30 and weighted target 248.50.
- Preserve original horizon through October 15, 2027, original-analysis reference
  186.01 and 30% upside threshold. No discounting or live-quote claim.
- Explicitly disclose that detailed underlying valuation assumptions have not
  been fully recovered or independently revalidated. Label temporary edits;
  reject probability totals other than 100%. Personal research remains separate.
- Update baseline valuation/scenarios and mobile checks; preserve prior work in
  version history. See NBIS-12-MONTH-MODEL.md for provenance and rollback.

## 2026-10-19 — NBIS target feasibility audit

Preserved original 12-month targets; clarified that the original conversation
contained working judgments rather than a full financial valuation. Added a
separate reverse enterprise-value/EBITDA worksheet with mandatory explicit
forecast inputs, economic convertible dilution and primary-source limitations.
See NBIS-12-MONTH-MODEL.md for provenance, outstanding work and rollback.

## 2026-10-19 — Calculated 12-month scenarios for all 11 companies

Added company-specific earnings, insurer equity-sales, and infrastructure
funding/dilution models with 20/50/30 default probabilities and a fixed
2027-10-19 horizon. Targets are computed from explicit assumptions; historical
NBIS targets remain separate. Added editable assumptions, probability checks,
sensitivity analysis, a full-universe overview and provenance/limitations.
Published research imports derive numeric targets from the same engine.
Corrected Gilat Telecom Q2 operating profit against the visually reviewed
Hebrew statement. See COMPANY-MODELS-2026-10-19.md for every input and source.

## 2026-10-20 — Focused news and research screens

News now starts with search and company selection, a compact source-status
disclosure, and a single-column feed. Additional filters and per-item evidence
are progressively disclosed; 12-item pagination, chronological/importance
sorting, source links, local read/saved/report actions and notification deep
links remain available. Exact repeated publisher suffixes are removed only from
the reading title; original titles remain in source details.

Research now starts with the company selector and four task views: overview,
valuation, personal research, and sources/tools. The overview prioritizes the
weighted target, thesis and next checks. Source packages, PDF/JSON workflows,
full provenance, previous versions and the historical NBIS calculator remain
available in their relevant views. Personal drafts stay mounted across views;
no storage migration or financial-assumption changes. Tabs support keyboard
navigation, and forms/readability are checked at 320/390/430px with 200% text.

Validation includes pagination/search reset, task switching without draft loss,
personal persistence and all existing model/PDF/import checks. Rollback: revert
this layout PR; persisted personal research requires no conversion.
