# AI Analyst proposal trust-boundary regression (Phase 3 follow-up)

This draft PR is stacked on draft PR #32, which itself depends on draft
PR #31. Do not merge or publish out of order.

## Threat and fix

The initial output validator accepted a packet's claimed `contentSha256`
without recalculating it. A stale or altered packet could therefore retain
its original digest and have a proposal accepted as though it cited the
original evidence. The validator now recomputes the same canonical JSON
digest used by `ai_research_packets.py` (sorted keys, UTF-8, compact JSON,
no NaN). A mismatch fails closed before checking any evidence citations.

An untrusted proposal also previously could label itself
`model-generated-unverified` without proof that an AI model was ever run.
Until an independently implemented, authenticated server-side AI execution
receipt exists, the validator accepts **only** `deterministic-no-ai`.
This prevents deterministic output from being presented as actual AI
analysis. The JSON schema remains a future wire-format superset; passing
schema validation alone does not satisfy the stricter runtime trust gate.

Even when a caller recomputes a digest after tampering, the validator rejects
accounting observations marked model-eligible or approved while the
repository lacks verified analyst approval infrastructure. It also rejects
input packets that permit valuation changes, claim an AI execution occurred,
or contain personal portfolio data.

**Important**: a SHA-256 digest proves equality of a particular JSON
snapshot, not authorship, issuer identity or authenticated analyst approval.
Only the trusted generator, issuer provenance validation, protected branch
review and eventually a separate model-run attestation can establish those
different guarantees. The proposed AI output still cannot update prices,
scenario probabilities or company research.

## Tests and CI

Four regression tests cover a false model-run label, a mutated financial
value, a mutated source digest, an altered research section, a recomputed
digest with forbidden approval flags, and invalid packet digests.

The previous PR #32 CI was cancelled during the GitHub runner's
`playwright install --with-deps chromium` apt downloads after the
10-minute job limit; no Python or JavaScript test failure was reported.
The read-only PR job limit is increased to 20 minutes to accommodate
transient browser-install slowness. It still cannot write to `main`.

The change does not run any AI service or change forecast history, research,
valuation targets, scenario probabilities, live data or branch protection.
