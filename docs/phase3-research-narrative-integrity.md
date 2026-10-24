# Phase 3 — analyst narrative collection integrity (draft)

This draft is stacked on PR #54 and its upstream drafts. It does not change
financial observations, analyst narratives, valuations, targets, probabilities,
forecasts, source PDFs, or `main`. It makes packet construction fail closed
when unverified research content is structurally corrupted.

## Finding

`research_for()` previously used `record.get("fields") or {}` and
`list(record.get("missing") or [])[:30]`. A falsey or absent sections value
could erase research excerpts without error; a string limitation would be
split into characters; more than 30 caveats would be silently truncated.
Malformed wrapper records could also trigger unrelated exceptions.

## Guardrails

- Require a structured research record and a nonempty set of recognized
  narrative sections; reject malformed section values.
- Require a real list of nonempty, bounded limitation strings; reject excess
  caveats instead of truncating them.
- Validate optional research date and scope *shape*, without claiming either
  is authentic.
- Preserve all valid existing narrative text and the
  `unverified-analyst-narrative` / `untrustedInstructions` markers.
- Keep the research file SHA-256 reference; never treat it as issuer approval.

Offline regression: `python3 -m unittest scripts/test_ai_research_narrative_shape.py`.
The existing read-only CI must also pass. No AI service is called.

**Trust limitation:** This is structural validation only. Unverified text
can still contain incorrect numbers, misleading assertions or prompt
injection. It remains data, not model instructions or approved issuer facts.
Keep draft; human review and upstream PR review are required before merging.
