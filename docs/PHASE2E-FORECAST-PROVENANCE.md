# Phase 2E — Prospective forecast archive and strict comparisons

The supplied PULSE research date (`asOf`) does **not prove** that a
forecast was written or locked before a historical earnings release.

The scheduled pipeline now archives each concrete monitored forecast
using a content-derived stable ID and stores its first *observed*
repository timestamp and commit SHA. Changing any financial forecast
input generates a distinct archived version; prior versions are never
overwritten. Legacy research `asOf` remains visible but is marked as
unverified for historical backtests.

The independent `forecast_actual_comparison.py` adapter only allows a
numerical difference if ALL of the following pass:

- company, metric, period, currency unit and accounting basis match;
- the forecast's first recorded calendar day **precedes** the official
  results publication day (same-day timestamps are blocked);
- the source-backed observed value has a matching, exact SHA-256
  **approved** entry in the merged analyst ledger, with no subsequent
  rejection;
- values are valid finite numbers.

If the current source evidence requires review, no numerical
comparison is emitted. The initial artifact is expected to have
blocked/no comparisons because historic results were published
before the first immutable archive. Synthetic tests verify the
actual arithmetic gate without presenting synthetic results as
historical performance.

Data artifacts:
- `public/data/forecast-archive.json`
- `public/data/forecast-actual-comparisons.json`

No model, probability, financial target, supplied PDF research or
user portfolio holding is modified. This PR is stacked on Phase 2C
(PR #26). The manual review ledger is in Phase 2D (PR #27); when
neither approved nor merged, comparisons stay blocked.

## Repository policy hard stop (2026-10-22)

GitHub currently reports `main.protected = false`. A decision entered into a
mutable JSON ledger is **Review Decision Recorded**, not verified analyst
approval. The production comparison pipeline deliberately passes
`verified_review_authority = False` and therefore emits **no numerical
performance surprises**, even when a JSON entry says `approved`. Test-only
calls exercise the math behind an explicit trusted-review flag using
synthetic evidence. Do not enable that flag in production until GitHub
rulesets requiring authenticated review are actually enforced and the
source-to-review attestations are validated.
