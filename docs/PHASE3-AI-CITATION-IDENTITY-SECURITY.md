# Phase 3 — unambiguous AI evidence citations (draft)

This security follow-up is stacked on draft PR #33, itself stacked on #32 and #31. Do not merge automatically.

## Finding

The review-only proposal validator built an evidence lookup with dictionary
comprehensions and `update()`. If two input records reused the same evidence
ID, the later record silently shadowed the earlier record, including across
financial observations and archived forecasts. A citation could then resolve
to an ambiguous or wrong evidence kind. Malformed collections and unhashable
citation IDs could also raise incidental Python errors instead of explicit
validation failures.

## Safeguard

- Require unique, nonempty string evidence IDs across all four namespaces:
  financial observations, archived forecasts, research sections, and existing
  valuation assumptions. Reject collisions rather than selecting a winner.
- Fail closed on malformed forecast, research, and valuation collections.
- Reject non-string citation IDs and interpretation/scenario references
  consistently as validation errors.
- Exercise duplicate financial IDs, cross-kind collisions, malformed
  collections, and unhashable references with offline regression tests.

The validator **does not** attest to issuer authorship, approval, source
authenticity, or factual correctness. Even with unique IDs and a valid packet
digest, every observation remains pending human reconciliation. No AI service
is invoked, no model or target is updated, and no permissions are expanded.

Run: `python3 -m unittest scripts/test_ai_analyst_review_contract.py`.
