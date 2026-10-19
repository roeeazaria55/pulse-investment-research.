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
targets. Detailed original revenue, multiples, cash, debt, dilution and private
asset assumptions were not fully recovered. The UI and baseline disclose this
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
