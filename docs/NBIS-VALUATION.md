# NBIS sourced, conditional valuation — 2026-10-19

Historical alternate model, removed from active UI at the user’s request.
The active model is documented in [NBIS-12-MONTH-MODEL.md](NBIS-12-MONTH-MODEL.md).

The worksheet replaces illustrative fixed cash/debt/share seeds with an explicit
June 30, 2026 → December 31, 2027 funding bridge and eight convertible series.
All financial amounts are USD millions and share counts millions. It is a
conditional analyst model, not an audited October balance sheet, company 2027
guidance, peer-multiple study, monthly liquidity model or DCF.

## Evidence and reconciliation

`src/data/nbis-valuation.json` contains individually labeled primary-source URLs.
Q2 statements (SEC exhibit 99.2, August 12) notes 12–14 establish share classes,
pre-funded warrants, RSUs/options, original versus carrying/accreted note amounts.
The separate operating review supports cash and H1 capex. Q1 shareholder letter
supplies 2026 revenue 3.0–3.4bn / exit ARR 7–9bn; Q2 letter reaffirms guidance.
ARR is never substituted for recognized 2027 revenue.

- June cash 8,042.1 excludes restricted 1,056.0. March NVIDIA proceeds and H1
  ATM proceeds are already included; no second cash credit is made.
- A+B outstanding 271.855218 + pre-funded warrants 21.065936 + approximate
  August exchange 15.8 + all unvested RSUs 6.234091 + all options 6.740600
  = conservative capital base 321.695845. Ignore exercise cash/forfeitures;
  this is neither current issued stock nor accounting diluted EPS shares.
- August closing: 5,750 gross new notes; pricing estimate with full option gives
  5,680 net. Exchange retires 400 original principal in each June series and adds
  approximately 15.8m shares without cash. Remaining original June principal is
  100 per series. July 775 facility is assumed fully drawn in presets and can be
  changed; unrestricted receipt/current cash is not asserted as verified.
- Remaining original notes: 13,450 before July facility/new funding. September
  2025 original 1,581.25 each includes exercised options; March 2026 original
  2,587.5 and 1,750 includes the exercised 2031 option only.
- IMPORTANT: June 2025 closing 6-K states maturity 120%/125%; Q2 table implies
  117.5%/122.5%. Use the higher closing terms, openly flag the unresolved source
  discrepancy (5m after the exchange). Conservative full future claims total
  15,756.875 before facility/new funding; not December-2027 contractual debt,
  accounting carrying value or a claim that all debt matures then. Deducting
  full maturity amounts without present-valuing is deliberately conservative.
- Use initial conversion rates, no future anti-dilution or make-whole adjustment.
  Economic dilution is hypothetical, not automatic legal conversion: 130% price
  tests, settlement election, legal restrictions/timing are not simulated.
- Reference 165.47 is October 16 closing history from Stock Analysis, corroborated
  by other historical tables in research. Finance endpoint returned an inconsistent
  live OHLC snapshot and is not used as a current quote. Discount dates remain
  October 19 → December 31, 2027 (actual days /365.25).

## Model and rationale

Revenue cases 7/11/15bn use exit-2026 ARR guidance as a scale anchor, followed by
explicit different 2027 delivery/utilization assumptions, not a claim ARR equals
annual sales. Group adjusted EBITDA margins 30/40/45% are below Q2 cloud-only
~50%; base relates to the group ~40% 2026 objective. EV/EBITDA multiples 8/12/16
are analyst judgments allowing growth but limiting premium for capital intensity,
maintenance and depreciation; implied sales multiples 2.4/4.8/7.2 are displayed.
No claim of observed peer pricing or statistically estimated probabilities.

Funding assumptions cover H2-2026 plus all 2027, with H2 capex 12/14.5/17bn,
2027 capex 18/25/32bn. Cash operating flows excluding net deferred-revenue
change 1.5/4.5/8bn include assumed interest, tax, rent and other working capital;
no noncash SBC deduction because diluted shares explicitly include awards.
Net advances 10/18/26bn are changes after revenue recognition, not gross
prepayments. Management's >9bn gross prepayments in 2026 are NOT simply added.
These assumptions are deliberately editable, not verified receipts.

Ending cash reserve 3bn; shortage financed 70/50/30% debt, rest equity at assumed
issue prices 120/160/200. Both sources incur assumed 2% gross issuance fees.
Unreported post-June transactions are absorbed into period-wide assumptions;
none are called verified current balances. Raises above remaining ATM capacity
are flagged as requiring additional issuance capacity. Successful financing is
conditional; intraperiod liquidity, new-loan pricing and restrictions can break
these scenarios. All options/RSUs are included conservatively before new awards
6/5/4m. Operating lease costs reduce assumed margins/cash: do not subtract lease
liabilities again under this after-rent EV convention. Uncommenced lease
obligations remain an execution/funding risk. Private investments receive zero
incremental value; not a claim they are worthless.

Economic dilution solves P*S + sum(max(conservative claim, conversion shares*P))
= enterprise value + end cash − nonconvertible senior debt. Iterate note
thresholds ascending; when adding conversion shares remove that series' claim.
Also display unconverted-note price. Zero floor means no residual equity under
these stressed assumptions; not a bankruptcy forecast or a current zero target.
Required multiple at historical reference includes the same dilution/discounting.

Preset results, rounded (not independent market observations):

| Case | Net funding gap, bn | Economic diluted shares, m | End-2027 value | Discounted value |
|---|---:|---:|---:|---:|
| Bear | 7.00 | 345.56 | $0.00 | $0.00 |
| Base | 5.50 | 348.13 | $105.44 | $92.04 |
| Bull | 3.50 | 388.71 | $263.65 | $235.17 |

Base requires ~18.81x EBITDA to justify the historical reference after discounting
versus assumed 12x. This is what the chosen assumptions imply, not a recommendation.
Personal research remains separate; worksheet edits are temporary, rendered only
when opened to avoid loading long forms in every company research view.

## Validation and rollback

Model tests cover funding closure/fees, cheaper equity dilution, no funding surplus,
all eight economic-conversion thresholds/no debt double count, reference break-even
identity, invalid inputs and no-positive-EBITDA case. UI tests clear/reset inputs.
The first local full run hit resource-contention timeouts (no assertion failure);
cap Vitest at two workers and allow 15s per test rather than unbounded workers/5s.
Run full JS/Python tests, production build and Chromium mobile checks at
320/390/430 including 200% text, all 11 baselines and PDF/import persistence.
Revert commit `Replace NBIS example seeds with sourced funding and dilution model`
to return to the prior worksheet; no personal-data schema changes.

Local validation completed: 79 JS tests, 61 Python tests and production build
passed. Chromium mobile suite passed at 320/390/430px, including 200% text,
invalid/reset model inputs, all 11 baselines and PDF/import persistence.
