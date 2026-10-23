# Phase 3 — AI Analyst review proposal contract

**No AI model is run or configured in this PR.** The validation function
`validate_ai_proposal(packet, proposed)` checks a future model's response
before it could be displayed to the researcher. A response is **never**
an approved financial fact, and passing validation **never triggers a
repository commit or a model update**.

Requirements:
- The output references the exact input packet content SHA-256.
- Every cited evidence ID must exist in the specific company packet.
- Numeric issuer evidence is cited by observation ID, which is tied to
  the collected official document SHA, raw value, definition and period.
- Research and model assumptions are cited separately; neither silently
  becomes a verified issuer fact.
- Hypotheses and scenario suggestions must cite previously declared
  evidence, include uncertainty and remain `requires-human-review`.
- Bear/Base/Bull proposed weights require an existing quantitative model,
  exactly three per-company rationales and weights totaling 100%.
- The output has no accepted keys for instructions, execution commands,
  automatic approvals, automatic investment orders or valuation edits.
- `proposedValuationAction` can only equal `no-automatic-change`.
- A separate server-side execution boundary and authenticated analyst
  workflow must be implemented and reviewed before AI analysis is enabled.
  No API token or paid AI provider is configured here.

Future pipeline: source evidence → verified input packet → isolated
model invocation (server-side, not GitHub Pages client) → strict validation
→ review-only proposal → authorized GitHub analyst PR → separately
reviewed model change, if justified.

The current input packets mark DLO source facts as needs-reconciliation
and `main` still lacks enforced branch protection. This contract does
not override either limitation.

Test from repository root:
`python3 -m unittest scripts/test_ai_analyst_review_contract.py`

Stacked on draft PR #31; must not merge ahead of its packet dependency.
