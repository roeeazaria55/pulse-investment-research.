# Phase 3 — fail-closed AI packet input collection shapes

This draft is stacked on PR #49 (which depends on PR #31). It does not
replace the issuer portal URL allowlist, nor does it approve any source.

## Finding

`build_all()` previously defaulted a missing issuer-company list to `[]`,
passed unvalidated observation/forecast collections to filters, and accepted
non-object entries in supplied research. A source changed from an array into
a string, object or mixed array could silently drop evidence or cause
incidental exceptions instead of a deliberate, auditable failure. In an
AI-research packet, an empty collection has a materially different meaning
from a corrupted source.

## Change

Require actual lists of JSON objects for the five existing source collections:
issuer companies, financial observations, archived forecasts, comparison
results, and supplied PDF research metadata. Require the four parent JSON
documents to be objects. An intentionally empty list remains valid; a
missing, substituted or malformed list fails closed with `ValueError`.

The offline regression test substitutes malformed shapes in each source
without writing or editing financial data. The existing four-issuer packet
snapshot and its DLO source-derived numeric checks must continue passing.

## Boundaries

This is structural integrity, **not** proof of issuer authorship, analyst
approval, or factual correctness. Packet content hashes are not signatures.
No AI execution, portfolio data, trading, valuation changes, price-target
changes, forecast changes or scenario-probability changes are introduced.

Run: `python3 -m unittest scripts/test_ai_research_packets.py`.
Keep this PR in draft until upstream draft PRs and CI are reviewed.
