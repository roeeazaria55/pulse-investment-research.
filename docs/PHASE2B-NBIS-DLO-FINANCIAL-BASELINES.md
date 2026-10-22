# Phase 2B — issuer Q2 2026 source baselines for NBIS and DLO

Two additional issuers now use the existing reviewed-source `FinancialResults`
presentation and date/company/period/basis comparison gates.

- **NBIS:** official August 12, 2026 Q2 exhibit 99.1 in SEC 6-K.
  Three-month consolidated revenue **$582.3m**, operating loss
  **($175.9m)**, reported operating cash flow **$2,246.1m**, and
  purchases of property/equipment and intangible assets **$5,657.4m**.
  The cash flow includes customer advances, so it is not a normalized
  operating-cash-flow or FCF estimate. The capital spending is *cash
  purchases of PPE/intangibles*, not total GPU financing commitments.
  Source: https://www.sec.gov/Archives/edgar/data/1513845/000110465926094568/tm2622968d1_ex99-1.htm
- **DLO:** official August 13, 2026 Q2 issuer release. Rounded reported
  revenue **$399.7m**, gross profit **$127.2m**, operating profit
  **$64.2m**, plus capital expenditure of **$9.910m** from the separate
  cash-flow reconciliation table, originally **(9,910) USD thousands**.
  The Q2 IFRS operating cash flow is **not mapped** and should not be
  substituted by the issuer's adjusted FCF metric. Values in the KPI
  summary have one-decimal precision; they are not the exact IFRS
  financial-statement cells.
  Source: https://dlocal.gcs-web.com/news-releases/news-release-details/dlocal-reports-second-quarter-2026-financial-results

Both extracts are **curated official evidence snapshots**, not
unattended retrieval. They remain explicitly pending analyst review
with no model/target/probability changes. Historical actuals precede
the October PULSE research and are blocked from backward-looking
surprise scores. The shared engine preserves the issuer-provided
three-month 2026 column, currency/units, source raw cell strings and
document links, and now accepts section links where issuer HTML has no
real printed page number.

The existing forecast comparison gates are reused, not weakened.
This change does not assert real-time automated promotion of source
facts. See the separate Phase 2 report-review-queue PR for the
scheduled-version intake pipeline.
