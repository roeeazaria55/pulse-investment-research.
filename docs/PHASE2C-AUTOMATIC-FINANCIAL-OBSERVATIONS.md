# Phase 2C — automatically proposed financial observations (DLO pilot)

The existing collector persists **real source content** in
`public/data/report-intake.json`, which already contains a successfully
downloaded official dLocal Q2 2026 GlobeNewswire release.

This PR adds `scripts/financial_observations.py`: a strict reviewed-layout
adapter that reads those collected **table cells**, derives the precise
three-month period from the financial table headers, parses source
figures and preserves their raw rows, source URL, SHA-256, source unit,
IFRS/issuer metric basis, accounting dates and review-version ID.
No financial amounts are hardcoded in the adapter.

Four pilot proposals can be generated from the stored DLO source:
**revenue**, **gross profit**, **cash from operating activities** and
**cash capital expenditures**. The extraction depends on the report's
reviewed HTML structure. If the structure changes, the adapter records
issues rather than guessing source columns. Negative capital spending
cash flow is converted to a positive investing amount and labeled
separately. The DLO source is marked revised in the saved collector
snapshot; its proposals are therefore **needs-reconciliation**, not
approved or used in valuation.

`public/data/auto-financial-observations.json` is produced after
`report_intake.py` and the versioned review queue in PR CI and the
scheduled public Pages workflow. The output is persisted between runs
and visible on DLO's research screen, with the original raw cell and
source link. Duplicate source SHA+metric+period identities do not
reproduce new proposals; a different content SHA creates a separate
historical proposal. Every proposal remains pending or requires
reconciliation.

The project remains a static GitHub Pages app. It has **no authenticated
public browser approval endpoint**, so this PR does not add one. It
also does not automatically revise the existing DLO displayed baseline
or compare pre-publication forecasts. Source-based financial
observations must be reviewed before any approved-map promotion.
No new issuer model, price target or Bear/Base/Bull assumption changed.

### Proof and limits

- Python regression tests use the *real stored official report-intake*
  document plus mutated synthetic fixtures. The live PR run also executes
  report collection and generates a proposed metrics artifact from the
  resulting retained source snapshot.
- This proves automatic extraction from a previously retrieved issuer
  document, not that every future document/issuer format can be parsed.
- Some live issuer endpoints currently return HTTP 403; failures retain
  previous source snapshots. The collector does not falsely treat 403
  as an unpublished report.
- Full analyst sign-off, broader metric schemas, secure review ledger,
  and prospective forecast comparison are separate Phase 2C milestones.
