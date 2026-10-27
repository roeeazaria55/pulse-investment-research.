# Financial intelligence sprint — 2026-10-27

Same branch and PR #60. Started from actual remote 13e1d01, which was 29 commits ahead of requested b41b8cb. No main merge, production deployment, paid AI, target, probability or portfolio modifications.

## Source acquisition

Real metadata/content scan on 2026-10-26 succeeded for FTAI SEC Company Facts, SEC 10-Q and issuer earnings PDF. Q3 was announced for October 29; Q2 is the latest identified published quarterly result. Official timing: https://ir.ftaiaviation.com/news-releases/news-release-details/ftai-aviation-ltd-announces-timing-third-quarter-2026-earnings

Original Company Facts bytes are retained in `public/data/source-evidence/ftai-companyfacts-20261026.json`. SHA-256: `1742e17a754230eb3611e6de60b5a1b58ccea139296c73a55d2fdd4668aa8a96`. Selected original accession facts are bound to this digest in report-intake. Other original PDFs are linked and source pages/digests retained, not all original binary files archived.

## Company matrix

Added columns compare against the requested b41b8cb baseline, including the three SMCI balance measures implemented before this working session. All observations require analyst review; none is model-approved.

| Company | Ingested source | Metrics | Added since requested baseline | Historical comparison | Verification | Model link / remaining gaps |
|---|---|---:|---|---|---|---|
| NBIS | [2026-04-01/2026-06-30](https://nebius.com/newsroom/nebius-reports-second-quarter-2026-financial-results) | 7 | operatingIncome, netIncome, operatingCash, capex, cash, debt | Same source/definition; exact per-metric periods | pending-review | Revenue, margin and financing inputs; no capacity/contract or AI segment extraction. Debt excludes leases. |
| META | [Q3 2026](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx) | 5 | netIncome, operatingIncome, operatingCash, capex | Same source/definition; exact per-metric periods | pending-review | Revenue/margin and cash PPE; CAPEX excludes finance-lease principal; balance-sheet debt not mapped. |
| DLO | [2026-Q2](https://rss.globenewswire.com/news-release/2026/08/13/3344936/0/en/dlocal-reports-second-quarter-2026-financial-results.html) | 6 | tpv, netIncome | None (reconciliation) | needs-reconciliation | Gross-profit driver (archived model distinct from supplied valuation); source reconciliation still required; no approved prior-period comparison or take rate. |
| FTAI | [Q2 2026](https://data.sec.gov/api/xbrl/companyfacts/CIK0001590364.json) | 6 | capex, cash, commonNetIncome, debt, operatingCash, revenue | Same source/definition; exact per-metric periods | pending-review | Financing/debt and earnings checks; Q2 earnings vs H1 cash flows, June/December balance comparison; segment metrics not mapped; accession adapter bounded to Q2. |
| LMND | [Q2 2026](https://www.lemonade.com/investor-relations-bo/wp-content/uploads/docs/LMND-Shareholder-Letter-Q2-2026.pdf) | 7 | netIncome, adjustedEbitda, grossEarnedPremium, inForcePremium, grossLossRatio | Same source/definition; exact per-metric periods | pending-review | Revenue/margin questions; premiums and loss ratio are operational measures, EBITDA is Non-GAAP. |
| SNDK | [2026-04-04/2026-07-03](https://investor.sandisk.com/news-releases/news-release-details/sandisk-reports-fiscal-fourth-quarter-2026-financial-results) | 4 | grossProfit, netIncome | Same source/definition; exact per-metric periods | pending-review | Revenue/margin checks; fiscal Q4, not calendar Q2; cash flow and debt still unmapped. |
| IREN | [2025-07-01/2026-06-30](https://iren.gcs-web.com/news-releases/news-release-details/iren-reports-fy26-results) | 5 | aiRevenue, netIncome | Same source/definition; exact per-metric periods | historical-baseline-pending-review | AI revenue, operating cash and CAPEX/funding inputs; FY2026 historical; customer advances distort operating cash; capacity/contracts still unmapped. |
| נקסט ויזן | [FY 2025](https://investor-relations.nextvision-sys.com/wp-content/uploads/2025/03/Periodic_Report_2025_isa.pdf) | 4 | operatingIncome, netIncome | Same source/definition; exact per-metric periods | pending-review | Annual activity/profit assumptions; FY2025 historical, not latest 2026 financials; latest-fetch identity failure retained transparently; backlog absent. |
| אנלייט | [2026-04-01/2026-06-30](https://enlightenergy.com/wp-content/uploads/2026/08/2Q26-Earnings-Release-Eng.pdf) | 5 | operatingIncome, netIncome, operatingCash | Same source/definition; exact per-metric periods | pending-review | Revenue/margin and cash generation; tax benefits separately disclosed; project capacity, debt and adjusted EBITDA not mapped. |
| בריינסוויי | [2026-04-01/2026-06-30](https://www.globenewswire.com/news-release/2026/08/12/3343549/17676/en/brainsway-reports-second-quarter-2026-financial-results-and-operational-highlights.html) | 4 | operatingIncome, netIncome | Same source/definition; exact per-metric periods | pending-review | Revenue and profitability; cash flow and debt not mapped. |
| גילת טלקום | [2026-04-01/2026-06-30](https://satcom-gilat.co.il/wp-content/uploads/2026/08/דוח-רבעון-2חצי-שנתי.pdf) | 5 | operatingIncome, netIncome, adjustedEbitda | Same source/definition; exact per-metric periods | pending-review | Profitability assumptions; ILS only, adjusted EBITDA explicitly Non-IFRS; cash flow and debt not mapped. |
| SMCI | [2026-06-30/2026-06-30](https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm) | 8 | accountsReceivable, cash, inventory | Same source/definition; exact per-metric periods | pending-review | No matching quantitative model; explicit manual research check for inventory and cash flow; CAPEX/debt not mapped. |

66 source-bound financial/operational measures across 12 companies. This is not full extraction of every statement item or confirmation that all twelve reports are the latest available.

## Automation and release boundaries

- Existing Collect → Extract → Validate → Compare → Research → Persist → Publish workflow reused. No new scheduler or publication path.
- Source failures preserve prior records; immutable research history deduplicates content, not polling timestamps. Existing history in pulse-data is seeded by the existing publish workflow; no initial local history is committed over it.
- Issuer-specific layout adapters fail closed for changed/ambiguous layouts; new report discovery does not imply universal automatic accounting mapping.
- GAAP/IFRS and adjusted metrics remain explicitly separate. Historical changes never become Beat/Miss without a valid dated forecast.
- Existing model fields are shown as review questions, without edits. The UI moves latest retained report evidence directly after the existing thesis.
- Production pulse-data persistence, deployed PWA and physical Android installation remain untested and require separate authorization.

## Verification

Local: 251 Python tests, 244 Vitest tests, TypeScript/production build passed. Final browser and remote CI evidence will be linked in PR #60 after completion.

Release decision: pending final browser/CI checks. Eligible only for review of a review-only research UI; not approval of financial metrics, merge or deployment.
