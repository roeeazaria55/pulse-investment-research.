# Restored NBIS 12-month model — 2026-10-19

At the user's explicit request, replace the active end-2027 valuation worksheet
with the original October 15, 2026 conversation model. Its recovered outputs are:
Bear $115 /20%, Base $235 /50%, Bull $360 /30%, weighted $248.50.
Historical analysis reference $186.01 implies 33.595% upside; the user's
weighted-upside threshold was 30%. This reference is from the previous analysis,
not a newly verified exchange quote. Horizon is October 15, 2027, exactly the
original 12-month horizon, not rolling 12 months from the restoration date.

Provenance is the October 15 conversation recovered from prior conversation
context. Do not invent a public source URL or imply corporate filings validate
targets. The original conversation explicitly offered working targets, not a full
financial valuation. Revenue, multiples, cash, debt, dilution and private-asset
bridges were not provided. The UI and baseline disclose this
and do not reverse-engineer assumptions to fit the targets. These are restored
historical judgments, not an independently revalidated valuation.

The new active JSON is nbis-12-month-model.json. A pure weighted-target function
validates finite inputs and 100% total probabilities, without normalization.
Inputs may be edited temporarily and reset; draft edits are labeled. Reference
price/date are editable with explicit historical/no-live-quote language.
No discounting of the 12-month targets or extra financing/dilution adjustments
are applied. The previous model is absent from active UI/baseline and retained
only in code history/research files for audit; it is not the user's model.

Verify weighted arithmetic, mismatched-probability rejection, restored defaults,
no appearance of old discounted outputs, company research preservation and
mobile 320/390/430 at 200% text. Run the existing JS/Python/build/browser checks.
Rollback: revert this PR's merge to restore the alternate end-2027 worksheet.

## Feasibility audit — October 19, 2026

Added a separate reverse-valuation worksheet alongside the preserved original
targets. Blank required inputs prevent historical balances from becoming an
implicit target-date forecast. It computes required enterprise value and EBITDA
multiples, not a replacement target. No additional discounting is applied.

Target-date cash, senior debt, future grants/equity, noncore assets, note
accretion sensitivity and annual EBITDA assumptions must be entered explicitly.
The starting share bridge includes June reported shares, prefunded NVIDIA
warrants, August exchange shares and all June options/unvested RSUs. It is not
a current fully diluted reported share count. Each convertible contributes the
larger of a cash-claim sensitivity and economic conversion value; legal tests,
settlement choices and make-whole provisions remain outside this sensitivity.
Full-maturity claims are an upper-bound stress, not debt accrued at the horizon.
The June-note upper bound retains the disclosed $5m source discrepancy.

Rechecked Q2 statements/letter and August closing/terms. June unrestricted cash
$8,042.1m, August estimated net proceeds $5,680m, and private-asset carrying
values $1,606.7m are context only. Neither gross advances nor historical cash
constitute target-date free cash. No incremental Avride value is added by
default. Source links are available in the worksheet.

Still needed: dated operating forecasts, cumulative cash/capex/funding bridge,
exact target-date accretion and dilution, and a justified valuation multiple.
The original $248.50 remains a historical judgment, not an audited fair value.
Tests invert the bridge through the independent economic-conversion solver,
check financing/dilution sensitivities, invalid inputs and undefined multiples.
Mobile checks exercise all inputs at 320/390/430px and 200% text.
Rollback: revert the audit commit; the original scenario worksheet survives.
