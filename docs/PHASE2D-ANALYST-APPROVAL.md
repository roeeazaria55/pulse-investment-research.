# Phase 2D — analyst decisions through GitHub PR review

PULSE is hosted as a **public static GitHub Pages** website. It has no
authenticated server endpoint for approving issuer facts. A button on
that page must not claim to perform an authorized approval.

The offline CLI `scripts/financial_review.py` accepts a review request
from a trusted analyst and checks it against the *exact* source-based
proposal in `public/data/auto-financial-observations.json`. It requires
stable observation/review-version IDs and an exact SHA-256 match, and
refuses to approve proposals marked as revised or requiring
reconciliation. It requires the numeric value, original unit,
source row, financial basis, period boundaries and HTTPS evidence.

### Manual flow

1. Read the source issuer financial statement and compare the
   proposal's raw row, column/period, currency and accounting basis.
2. Create a local JSON review request (do not commit private notes).
   Example:
   `{"observationId":"observation:<id>","reviewVersionId":"review:<id>","sourceSha256":"<64-character hash>","decision":"needs-reconciliation","reason":"Issuer document revised; reconcile exact source cells","evidenceUrl":"https://<verified official source>"}`
3. On a separate GitHub branch run:
   `python3 scripts/financial_review.py --request ./review-request.json`
   This appends a proposed event to
   `public/data/financial-review-ledger.json`.
4. Submit that ledger diff through a GitHub PR requiring maintainer
   approval. Only after merging the PR into the protected publication
   branch does the ledger represent a repository-accepted decision.

Do not represent the request's self-supplied timestamp or evidence URL
as proof of analyst identity. GitHub authorization, reviewer activity
and merge history provide the actual actor/approval audit trail.

The initial ledger contains **no approved metrics**. The stored
dLocal Q2 release currently has a revised source hash and so cannot
receive an automatic approval. The CLI supports explicit
`rejected` and `needs-reconciliation` decisions and never modifies
price targets, investment assumptions or forecast probabilities.

This PR is stacked on the phase 2C extraction proposal PR; do not
merge it ahead of that dependency.
