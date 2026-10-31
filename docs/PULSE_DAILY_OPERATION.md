# PULSE daily operation

## Schedule

Scheduled news and official report collection runs at 08:00 and 19:00 in
Asia/Jerusalem. Scheduled AI queue admission runs at 08:30 and 19:30 in the same
zone. GitHub supports timezone-aware cron; delays are possible. The 30-minute
gap is a buffer, not a dependency guarantee. If collection is delayed or fails,
AI sees the most recently persisted queue and remaining work waits for a later
window. Code-push/manual collection triggers remain available.

## What happens

1. Free collection discovers news and official issuer documents for the 12
   registered companies. Source allowlists, byte/time limits and retained
   history apply. Discovery does not prove that the latest filing was found.
2. Supported tables/XBRL become unapproved financial proposals. Bounded source
   excerpts supplement them. Missing, ambiguous or unavailable evidence stays
   explicit; previous successful records survive fetch failures.
3. Changed financial candidates reconcile into a persistent queue. Completed,
   pending-review, failed or reserved tasks are not automatically retried.
   The initial backlog may contain historical reports, not only new filings.
4. Each scheduled AI run processes at most ONE eligible source-supported job.
   The new credential environment allows main only; protected main, owner-merged
   CI, active-month policy and both activation switches must pass. Unknown
   billing holds stop scheduled spending.
5. The runner commits a cost reservation before calling OpenAI. The maximum
   output ceiling is 50,000 tokens, not mandatory usage. Request estimate must
   be <=$1 and recorded+reserved spending plus the quote <=$9. The $10 planning
   budget retains $1 buffer; this is not an OpenAI account hard billing cap.
6. Successful responses must satisfy structure, exact packet evidence IDs,
   analytical constraints and publication restrictions. Cost is recorded even
   if a response is invalid. Valid results are saved as unapproved drafts.
7. A later successful Pages publication makes saved drafts visible in PULSE.
   The AI workflow does not itself deploy the website. In normal timing, an AI
   draft may become visible only after the next 08:00/19:00 site publication.

## Where to read

Research -> choose the company -> Overview/סקירה -> latest research update ->
AI analysis/ניתוח AI. This includes ten sections, evidence and limitations.
Source-data drafts and queue status appear nearby; they are not the AI report.
Settings show recorded/reserved cost after ledger publication. Pending review
is not approved research. Target prices and scenario probabilities never change
just because a draft exists.

Analyses written in a ChatGPT conversation do not automatically transfer to
PULSE. Only the GitHub pipeline's persisted drafts, or a separate explicit
research import/publication flow, appear in the app.

## Current permission period

Standing draft permission is limited to October and November 2026 UTC. It does
not renew itself into December. Both runtime flags remain emergency stops.
Publication and approved research updates continue to require separate owner
authorization. No new model call was used to change this schedule.
