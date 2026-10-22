# Phase 2F — Deterministic source-based research update proposals

The scheduled pipeline can now produce a **review-only factual brief**
from automatically parsed issuer data and the forecast comparison
block reasons. It includes source URL and SHA-256, raw and converted
units, accounting basis, period, status and the analyst question
specific to each metric.

It must not fabricate quarter-on-quarter growth or model impacts from
a single quarter, and it makes no price-target changes. For a currently
revised/awaiting-review source it clearly says that no thesis
conclusion has been established. The JSON field
`aiAnalysisEnabled: false` is deliberate: no secure model service
has been configured and no API key is exposed to the browser.

The build produces `public/data/research-update-proposals.json` and
persists it only after official collector + review queue + financial
observation + forecast archival steps finish successfully. New report
source hashes create distinct proposal IDs rather than modifying an
older research proposal in place.

The full automatic pipeline remains a pilot for reviewed issuer
table layouts; other issuers and new report structures may produce
no mapped proposal. A green CI test is not proof of real-time
detection of future earnings reports.

Stacked dependencies:
- PR #26: official collected source to typed proposed financial facts;
- PR #28: no-hindsight forecast archive and approved-only comparison;
- PR #27: optional maintainer-reviewed decision ledger.

This PR is draft-only, targeted to PR #28's branch, and should not
merge to main until dependencies are reviewed and merged.
