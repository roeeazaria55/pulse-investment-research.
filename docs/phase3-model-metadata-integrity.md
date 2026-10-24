# Phase 3 — untrusted valuation model metadata integrity (draft)

This draft stacks on PR #58 and its upstream drafts. It covers a separate
trust boundary in the **offline** DLO/NBIS/IREN research packet generator.
SMCI continues to have no structured active valuation model.

## Finding

The generator previously copied `method`, `methodNote`, `driverLabel` and
`quoteCurrency` from analyst-model JSON into an AI research packet without
checking type, length or control characters. A malformed or adversarial source
could present fake approval-like labels, invalid currencies or control-character
injections as if they were ordinary analyst metadata.

## Guardrails

- Accept only the two currently supported model method identifiers:
  `earnings` and `funded-ev`. New methods require explicit reviewed support.
- Require nonblank bounded descriptions and labels; reject ASCII controls,
  backslashes (including escaped instruction separators) and Unicode
  bidirectional override/isolation controls.
- Validate both quote and report currency fields as three uppercase letters.
  This is **syntax only**, not proof of a valid ISO currency or exchange rate.
- Reject the entire packet build on invalid model metadata rather than
  silently emitting null or substituting values.
- Preserve all existing valid metadata, scenarios, reference prices, targets,
  probabilities, research narratives and source files **verbatim**.
- Keep `approvedTargetPrice: null`, `noAutomaticUpdate: true` and the
  unverified analyst-model role. No approval or AI analysis is implied.

## Offline regression

`python3 -m unittest scripts/test_ai_model_metadata_integrity.py`

Normal read-only PR CI must pass before human review. These structural checks
do not authenticate issuer facts, prove analyst approval, validate economics,
or prevent every semantic prompt-injection attempt. The downstream AI analyst
must continue to treat all research and model text as untrusted data.

No API requests, paid AI, credentials, changes to `main`, or merges.
