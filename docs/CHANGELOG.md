# PULSE change log

Each numbered change below is kept in its own Git commit. The pull request lists
exact commit IDs and CI results. Revert an individual commit to undo that change;
revert the merged pull request to restore its preceding deployed code. Before
reverting, inspect any later changes that depend on the same code. Public source
snapshots update separately; personal browser holdings, notes and research are
not repository files and are never modified by these collector changes.

## Quality 1 — explicit document metadata

- Replaced generic ENG/HEB/View File labels with an issuer-page heading, nearby
  document heading, or a labeled filename fallback. Whitespace is normalized.
- Added source labels, language, title basis and document-period hints. A year in
  a path is never a publication date. A filename-derived period is marked as a
  hint requiring review.
- Publication dates require a distinct index time/date or explicit page
  publication metadata, with the source URL retained. Modified/event dates are
  not substituted. Adjacent cards cannot lend each other a publication date.
- Existing collected links keep IDs and first-collection timestamps. Failed
  sources retain prior records. Images/styles/scripts are rejected as documents.
- Added parser and provenance regression tests. PR checks collect live public
  metadata read-only before validating and building the exact test snapshot.
- Rollback: revert the commit named `Fix document labels and publication-date
  provenance`; retained earlier version-1 snapshots remain readable.

## Quality 2 — verified issuer distribution and Gilat coverage

- Added GlobeNewswire organization indexes for IREN, DLO, FTAI and BrainsWay.
  A matching publisher badge in the same card is required before collecting a
  release; unrelated publishers and law-firm mentions are rejected.
- Added Gilat Telecom's verified Satcom-Gilat investor financial/immediate
  reporting pages, including explicitly linked Maya reports. Dates must appear
  in an individual report entry; URL years are not used.
- Distributor releases are labeled separately from company-hosted IR documents.
  Registry additions do not imply successful collection; live CI reports actual
  availability, and blocked or empty sources remain visible.
- Validation: 51 Python tests, 60 JavaScript tests and production build passed.
- Rollback: revert `Add verified issuer distribution and Gilat investor sources`.
  The preceding metadata commit is `4129dd62d42f274c49f866d95efd35797627d43e`.

## Quality 3 — whole-answer import and recovery verification

- Import now accepts a complete ChatGPT answer containing exactly one fenced
  JSON object, while retaining company, date, field and source validation.
  Ambiguous multiple code blocks and malformed/truncated JSON are rejected.
- Preview and explicit field selection still precede any draft change.
- Added regression coverage for prior-version restoration, personal-note
  preservation and persistence compatibility. Extended mobile browser checks
  to save, reload, restore the previous thesis and retain the imported version.
- Validation: 62 JavaScript tests and production build passed locally; live
  source collection and full browser checks run in GitHub Actions.
- Rollback: revert `Accept single JSON answer blocks and verify research recovery`.
  Coverage commit: `63777de8375259bd8e952e9f09db5d505b34ad3f`.
