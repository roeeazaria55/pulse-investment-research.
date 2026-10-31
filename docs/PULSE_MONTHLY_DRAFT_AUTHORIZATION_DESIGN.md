# Proposed monthly authorization for unattended drafts

Status: design for review; not activated or implemented as a bypass.
Existing exact-run owner approval remains mandatory.

A future owner-approved monthly grant should contain: exact UTC month,
repository and protected main workflow revision, model allowlist, company
allowlist, maximum call estimate $1, cumulative $9 start ceiling, $10 planning
budget, no retry permission, and permission to create unapproved drafts only.
The grant must reference an owner-approved GitHub environment run and verify
that run, workflow, actor, approval history and merged CI through read-only
GitHub APIs on every use. A mutable JSON flag alone is not authorization.

An unattended worker needs a separately configured credential environment
restricted to main and a validated grant; the existing reviewer-protected
pulse-ai-paid environment cannot deliver its secret without per-run approval.
The existing release environment must retain owner review. Do not remove
reviewers from either existing environment to make schedules execute.

Every request must still commit its budget reservation before network access,
use serialized spending, bind the source packet, record malformed output cost,
stop on unknown billing, and expose $5/$8 notices. A grant expires at UTC month
end, cannot authorize research publication/targets/scenario changes, and needs
an immediate revocation path. Active months default empty until selected.

Required acceptance tests: forged/replayed/revoked grants; altered main or model;
month rollover; duplicate sources; unknown costs; concurrent ingestion; and
publication attempted with a draft-only grant. Secret/environment setup and a
reviewed implementation are still required before calling this fully automatic.
