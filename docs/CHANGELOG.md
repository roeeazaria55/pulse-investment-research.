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
