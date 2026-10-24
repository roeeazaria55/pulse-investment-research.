# Phase 3 — supplied research PDF pointer integrity (draft)

This change is stacked on draft PR #53 and **does not** alter source PDFs,
valuation models, scenario probabilities, price targets, forecasts, or `main`.
It makes the existing `legacyResearchPdf` pointer fail closed when the
supplied-research registry is ambiguous or its claimed file identity cannot
be reconciled with repository content.

## Finding

The AI packet builder previously took the first matching `companyId`,
silently omitted malformed PDF names, and hashed any existing file without
checking the registry's declared SHA-256. A substituted PDF could therefore
be presented as the expected supplied research, while duplicate or
cross-issuer metadata could silently choose the wrong record. The original
file check also followed symbolic links.

## Guards and behavior

- Require exactly one supplied PDF record per selected issuer, with both
  `ticker` and `companyId` matching the official registry entry.
- Reject unsafe or malformed filenames and missing/invalid lowercase SHA-256
  claims rather than silently dropping the pointer.
- Reject symlinked public/research paths or PDF files and non-regular files.
- When a PDF exists, recompute its SHA-256 and compare it to the registry
  digest before emitting a `sourceFile` reference.
- Preserve the existing `unavailable` status when a well-formed registry
  record refers to a PDF not present in the repository. IREN currently has
  no supplied PDF record and still emits `null`.

**Limitations:** A matching hash proves byte identity against the checked-in
registry, not issuer authenticity, authorship, PDF safety, factual accuracy
or analyst approval. No PDF content is parsed into financial observations.
The symlink checks target ordinary repository/CI conditions and do not
promise race-free behavior under a hostile concurrent filesystem writer.

Offline regression command:

`python3 -m unittest scripts/test_ai_pdf_reference_integrity.py`

The read-only PR workflow runs `unittest discover` and the full application
checks. Human review of this and all upstream stacked drafts is required.
**Keep the PR in draft; do not merge.**
