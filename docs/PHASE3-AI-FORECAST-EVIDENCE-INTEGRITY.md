# Phase 3 — archived forecast evidence integrity (draft)

This change is **stacked on draft PR #51**, which itself depends on #49 and #31.
It is read-only input validation. It does not approve historical predictions,
change the original forecast archive, change any valuation/scenario, or invoke AI.

## Finding

The packet builder's `forecast_history()` silently skipped an archived
forecast for a selected issuer when its `point.value` was missing, malformed
or non-numeric. It also accepted a mismatched `ticker` when `companyId`
matched, and copied incomplete archive metadata into the AI input packet.
A corrupted archive could therefore make evidence disappear from the packet
without any explicit failure.

## Guardrails

- Every forecast belonging to DLO, NBIS, IREN or SMCI must have a matching
  ticker/company identity, unique forecast ID, numeric finite point, complete
  units/basis/period, and basic provenance metadata.
- The archive timestamp must be a parseable timezone-aware ISO timestamp;
  the recorded commit must be a 40-character hex identifier; the claimed
  research date must be a valid ISO date.
- `canBeUsedForHistoricalBacktest` must explicitly remain `false`.
  The output always labels chronology as `research-asof-unverified`.
- A ticker/company mismatch, malformed forecast or duplicate ID raises an
  error instead of producing a packet with silently missing evidence.
- Tests preserve the existing counts (DLO 4, NBIS 3, IREN 0, SMCI 1),
  validate unchanged source values, and inject malformed source records.

**Trust boundary:** ISO timestamp format and hex-commit format are not
cryptographic proof that a forecast was archived before publication.
Content SHA-256 is not an issuer signature. No automatic approval or
historical backtest is granted.

Offline test: `python3 -m unittest scripts/test_ai_research_packets.py`.
Review upstream draft dependencies and CI before considering any merge.
