# Phase 3 — existing valuation-model packet input integrity (draft)

Stacked on draft PR #56. This is a read-only input-boundary hardening
change for DLO, NBIS and IREN. SMCI has no structured active valuation
model and must remain `null` in the research packet.

## Finding

The AI packet builder accepted an absent `scenarios` key as an empty list,
and exported scenario fields with `.get()` even when probabilities, input
drivers or rationales were missing or malformed. A corrupted local analyst
model could therefore appear as a complete set of assumptions to a
downstream analyst.

## Guardrails

- Require the model version, ticker and issuer ID to match the registry.
- Require exactly one each of `bear`, `base` and `bull`, with nonempty
  labels, rationales and input-driver objects.
- Require finite numeric input values and probabilities in the inclusive
  0–100 range, totaling 100 (without enforcing fixed scenario weights).
- Fail the entire offline packet generation on malformed model evidence;
  do not drop or replace a scenario with defaults.
- Preserve existing scenario order, weights, input values and rationales
  verbatim for all valid issuer models.
- Retain `approvedTargetPrice: null`, `noAutomaticUpdate: true` and
  `existing-analyst-model-not-issuer-fact` in every emitted model pointer.

Run `python3 -m unittest scripts/test_ai_model_input_shape.py` locally.
Normal read-only pull-request CI is required before review.

**Trust boundary:** shape validation does not authenticate the model's
provenance, validate economic assumptions, or authorize an AI to revise
targets, forecasts or probabilities. No paid model/API invocation, financial
source edits, or main-branch changes are part of this PR.
