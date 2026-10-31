# Reading hierarchy and model-review notices

The home screen and each company's overview show a short model-review inbox.
A notice means inspect assumptions, not replace a target or approve AI output.
It currently detects three explicit signals from validated retained documents
and the public research baseline:

- a dated, extracted issuer document published after the baseline and not cited
  by it; future, undated, unread and foreign-company documents do not trigger;
- a cited document's content version changes after its prior version was still
  observed after the baseline date; wording does not assume financial materiality;
- a dated valuation horizon has expired (a missing horizon is not invented).

One notice per company links to its valuation tab and, when available, the
issuer document. IDs bind company, research baseline and document hash so a
new version can reappear after an older notice was read. Read acknowledgements
stay in this browser, are capped, and are not review approval or model updates.
Source coverage and metadata can be incomplete. This is not an exhaustive
materiality detector, continuous browser monitoring, or a phone/push service.
Notices become visible on opening PULSE after a source snapshot is published.

## Progressive disclosure

Home macro, daily briefing, calendar and engine status are expandable rather
than full blocks stacked on first load. Relevant briefing/calendar deep links
still open the corresponding section.

Company overview keeps thesis, existing target and the short AI draft heading.
Full AI text, source workflow/queue/history, accounting detail, thesis metrics
and the full original report open separately by reader choice. Existing tabs,
personal draft editing, targets and all underlying research remain available.
The full report no longer opens by default. Native details/summary controls
remain keyboard accessible with touch targets and bounded reading widths.

Both dark and light modes are supported. Existing browser checks explicitly
open disclosure groups before testing the retained financial data; initial
collapsed state is checked instead of assuming a long report is visible.

## Five usability additions

- Home prioritizes up to three actionable updates. Workspace statistics and
  extra headlines are expandable; partial endpoint failures remain explicit.
- Every company overview begins with the business thesis, three clear actions
  (read, valuation, sources), review reasons and the existing target. Existing
  research tabs and personal draft editing remain unchanged.
- Content badges distinguish verified archive publications, AI drafts, pending
  source data and retained baseline research. A baseline is not relabeled approved.
- Clean reading opens a single copy of the report in a focus-managed dialog.
  Font choice, chapter selection and a local resume point are supported for
  supplied reports, other baseline text and full AI reports. Financial text is
  not changed by the controls. The long chapter index is optional.
- The central task inbox combines model-review signals, newly retained reports
  without structured facts, latest AI drafts per company and high-importance
  official-metadata news. All tasks can be opened from the home card without a
  new navigation tab. A local completion marker can be reversed in the inbox;
  it is not a server approval. A new AI/source version has a new task identity.

The last-visit timestamp, task completion, font and chapter state stay on this
browser. Nothing is sent to a portfolio/profile endpoint or notification service.
The task center routes to each registered company's relevant research tab; AI
tasks open the draft disclosure. New task detection is not an investment action.
