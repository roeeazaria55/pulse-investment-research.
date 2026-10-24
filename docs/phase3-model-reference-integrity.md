# Phase 3 — historical model reference integrity (draft)

This draft stacks on PR #57. It tightens a separate trust boundary:
`valuationModel.referencePrice` was previously copied from a local model
without checking its shape, issuer-specific URL or historical date.

## Scope

- Require the existing model's analysis/horizon dates to be valid ISO dates
  with the horizon after the analysis date.
- Require the historical reference to contain exactly price, date, URL and
  label; require a finite, positive numeric price and a reference date no
  later than the model's claimed analysis date.
- Allow only the existing HTTPS historical-quote provider hostname and the
  exact ticker-specific `/stocks/<ticker>/history/` path; reject forged
  domains, credentials, ports, fragments, queries, controls and backslashes.
- Fail the entire offline packet build on malformed provenance instead of
  silently exporting a null or spoofed quote reference.
- Preserve valid reference prices and dates **verbatim** for DLO, NBIS and
  IREN. SMCI still has no structured valuation model.

## Verification

`python3 -m unittest scripts/test_ai_model_reference_integrity.py`

CI should run all existing read-only checks before human review.

**Important:** An allowed URL is a provenance pointer, not an authenticated
market quote or a real-time price. The `referencePrice` field is an
unverified historical reference. This PR does not fetch market data, invoke
an AI API, approve research, or alter any financial model, target, forecast
or Bear/Base/Bull probability. No `main` writes or merges.
