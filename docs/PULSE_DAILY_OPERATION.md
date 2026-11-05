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
   CI, active-month policy and both activation switches must pass. An unresolved
   hold blocks another paid analysis of the same report and counts against the
   budget, including after a month rollover.
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

## Recovery after an API failure

- A confirmed `rate_limit_exceeded` can use one separately reserved retry.
  The runner waits at least two seconds and honors a longer valid
  `Retry-After` up to 60 seconds. A longer wait, no available retry budget,
  or a second failure ends the run. `insufficient_quota` and unclassified
  429s receive no automatic retry. Each dispatched slot has its own client
  request ID and can only be dispatched once by the runner.
- A request without a usage receipt remains reserved. The runner releases a
  retry slot only when its private dispatch journal proves it was never sent.
  An interrupted run is marked failed on the next admitted run, and its holds
  stay in the budget. A new task for a different issuer can still run.
- For an uncertain hold, match the request ID and project/time to authoritative
  billing evidence. A missing receipt, HTTP 429, or a temporarily unavailable
  billing view cannot authorize release. Keep the report out of paid replay
  until the hold has been reconciled in a reviewed ledger change. The existing
  owner-approved retry for a settled invalid response remains separate.

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
