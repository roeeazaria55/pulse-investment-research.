# Published research baseline

NBIS has a dated, static research baseline authored in ChatGPT from five issuer
sources on 19 October 2026. It is available to read in the research screen without
copying a file. It is not an automated AI feed and does not assert exhaustive
coverage, current valuation or a price target. Original financial observations,
management forecasts, qualitative scenarios and missing inputs are labeled.

Opening the screen does not mutate personal research. The compare button opens
the existing field preview; the user may choose fields to apply to their draft.
The existing save/autosave and three-version history remain authoritative.
Personal notes are never replaced by baseline adoption. Other companies do not
show the NBIS baseline. The shared baseline is public repository data; no user
portfolio, notes or local research are uploaded.

Validation: 64 JavaScript tests and production build passed locally. New tests
exercise no write on render/preview, correct issuer, explicit application,
retention of personal notes and a restorable previous thesis.

Rollback: revert the commit titled `Embed dated NBIS baseline in the research
screen with optional field comparison`. Reverting the published card does not
undo a user's earlier deliberate local adoption; use research version history
for that. No data collector, schedule, secrets or notification behavior changes.
