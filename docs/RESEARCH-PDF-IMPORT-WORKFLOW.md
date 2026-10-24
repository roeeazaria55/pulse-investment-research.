# PULSE — importing the seven newly supplied research PDFs

This workflow is intentionally manual and review-gated. **No valuation, trade, user portfolio or primary-source fact is approved by this import.** The ZIP was generated from the seven user-supplied original research PDFs on 21 October 2026. Existing five research PDFs in the repo must not be replaced.

## Input

`PULSE_Research_Import_Package_2026-10-21.zip` (provided in the ChatGPT conversation; download it locally). It contains original PDFs, extracted per-page text and `manifest.json`. The seven SHA-256 values and page counts are recorded in `src/data/newResearchSourceManifest.json`, but the GitHub repository **does not yet contain these seven new PDF bytes**.

## Process

On a checkout of the feature branch `pulse/phase0-research-audit-20261021`:

```bash
python3 scripts/validate_research_bundle.py PULSE_Research_Import_Package_2026-10-21.zip
python3 scripts/stage_research_bundle.py PULSE_Research_Import_Package_2026-10-21.zip --output work/research-staging
python3 scripts/import_research_pdfs.py PULSE_Research_Import_Package_2026-10-21.zip
# Review the seven expected names; only then explicitly write:
python3 scripts/import_research_pdfs.py PULSE_Research_Import_Package_2026-10-21.zip --apply
git status --short
```

Review changes before committing on the feature branch. The importer refuses to overwrite a PDF that has a different checksum, and the default invocation writes nothing. Imported files remain **independent research, unverified against issuer filings**.

Run `python3 -m unittest discover -s scripts -p 'test_*.py'`, `npm test`, `npm run typecheck`, and `npm run build`.

## After the PDF commit

1. Reconcile repo copies with `src/data/newResearchSourceManifest.json` by hashing the actual committed binary files.
2. Update `researchIntakeRegistry.json` statuses only after the bytes are truly committed; do not infer success from a downloaded ZIP.
3. Create immutable full-text reading snapshots that retain sections, paragraph order, table columns and notes. Check RTL table ordering against the original PDF pages.
4. Reconcile and only then propose structured scenario values: reference date, USD/ILS/agorot, common share versus ADS, 2027 versus 2028 profit bases, net debt and expected dilution.
5. Stage an explicit candidate diff and human review before promotion to the active website valuation.
6. Ensure the PR read-only CI passes and review the resulting mobile layout. Merging can deploy through the existing Pages workflow, so do not merge merely because import metadata exists.

## Constraints

No changes to user localStorage, portfolio, watchlist or personal notes. No direct copy of user files into publicly deployed assets without review that they are appropriate for a public GitHub Pages website. The uploader/reviewer must verify permission to distribute PDF bytes publicly before using `--apply`; extracted page text can remain in local staging while this is resolved.

## ZIP member integrity (Phase 2C)

Validation requires exactly one `manifest.json`, seven referenced `originals/*.pdf` files, and seven referenced `extracted/*.pages.json` files. Explicit empty `originals/` and `extracted/` directory entries are permitted. Unreferenced files or directories and ZIP members marked as symbolic links or other special filesystem types are rejected, even when the referenced PDF hashes match. This prevents hidden payloads or misleading filesystem metadata from passing a manual research package check; it does **not** authenticate research claims, authorship, or redistribution rights.
