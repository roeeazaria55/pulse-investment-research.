# Automatic draft authorization

Implemented worker path, pending deployment and credential setup. The owner's
explicit request authorizes recurring draft generation within the existing
budget. Protected main's reviewed policy is the standing authorization; it
is not derived from model output or an editable website control.

The scheduled worker uses `pulse-ai-drafts`, a NEW environment restricted to
the branch `main` (no tags/wildcards), with no required reviewer. Manual paid
trials retain `pulse-ai-paid` and its exact-run owner approval. Research release
retains `pulse-research-release`; its reviewer must not be removed.

`config/pulse-ai-policy.json` explicitly permits October/November 2026 UTC and
`automatic-drafts` only. It expires on 1 December UTC. Changes require an owner
merged PR and successful CI. Two runtime flags remain emergency off switches:
PAID_AI_ENABLED and PAID_AI_SCHEDULE_ENABLED must both be YES.

Every scheduled call checks the current protected main, successful owner-merged
CI, original protected paid environment, exact current run and owner actor,
new environment's sole main branch rule, active month, current queue and
recorded/reserved budget. Reruns, manual events using this path, unknown billing
holds and automatic retries are blocked. $1 estimated/call, $9 start-block and
$10 planning budget remain; provider billing is not a hard capped account.

## One-time setup after CI and merge

Create environment `pulse-ai-drafts`; choose Selected branches and tags and
allow exactly branch main. No reviewers for this draft-only environment.
Add OPENAI_API_KEY there (GitHub cannot reveal/copy the existing secret).
Keep the two existing environments' protection unchanged. Enable both runtime
flags only once the new policy and secret environment are ready. Scheduled
runs then create unapproved drafts without per-run approval. NO action here
approves a model, publishes research or changes targets/scenario weights.

The first free admission and security checks must be observed; missing/malformed
settings fail closed before spending. Verify the first automatic result/cost
and website publication. No new paid call or environment change was performed
while writing this code. Revoke through either flag immediately or a policy PR.
