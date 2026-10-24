# Phase 3 — comparison evidence integrity (draft)

This change stacks on draft PR #52 (and its draft dependencies). It changes
only **AI research input packet validation and auditability**, not the underlying
forecast archive, accounting observations, valuation models, target prices,
scenario probabilities or research conclusions.

## Finding

The packet builder previously filtered `forecast-actual-comparisons.json`
by observation ID and copied any `blocked` record without checking that the
forecast ID existed, belonged to the same issuer and metric, or was unique.
Other statuses could silently disappear. The packet's `sourceRefs` also
omitted the comparison JSON and supplied-research registry, so a consumer
could not identify the exact input versions from packet references.

## Guards

- Validate **all** comparison records before generating any issuer packet:
  both IDs must exist and be unambiguous; each pair must be unique; issuer and
  metric must match.
- Accept only `blocked` status, null `difference` and `percent`, and
  nonempty unique reasons from the current fixed comparator vocabulary.
  Any `comparable`, fabricated reason, orphan reference or malformed record
  fails the entire build. A new comparator reason requires an explicit
  reviewed contract update.
- Keep matching blocked comparisons marked
  `verification: unverified-derived-comparison` and `modelEligible: false`.
- Include SHA-256 references for both the comparison file and
  `src/data/suppliedResearch.json` in every packet.

**Trust boundary:** A source hash establishes content identity, **not**
authorship, correct accounting, approval or chronology. Even syntactically
valid blocked comparisons are not issuer-confirmed facts. There is no
backtesting approval, AI execution or automatic model update.

Run offline regression checks:
`python3 -m unittest scripts/test_ai_research_packets.py`.

Human review of the stacked draft PRs and CI is required before any merge.
