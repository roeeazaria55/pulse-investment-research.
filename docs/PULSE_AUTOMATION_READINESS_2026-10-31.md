# Evidence depth and scheduled research readiness

This change expands retained report content and admission controls. It does not
activate recurring spending, approve research, or verify extracted numbers.

## Evidence

- Intake now retains every currently supported inline-XBRL concept, including
  cash PPE purchases, common-shareholder income and debt instrument carrying
  amount. Retention rotates across concepts so repeated contexts cannot crowd
  out CAPEX/debt. Ambiguous contexts still fail financial mapping.
- Financial proposals may contain up to 16 measures instead of 8. Existing
  issuer/date/unit checks remain; debt instrument carrying amount is not total
  debt or all liabilities. No sum of overlapping debt tags is inferred.
- Up to six verbatim keyword windows (800 characters each) cover liquidity,
  cash flow/CAPEX, outlook, internal controls, legal disclosures and notes.
  These are excerpts of retained documents, not complete disclosure reviews,
  live legal verification or unrestricted internet search. A keyword may occur
  in a contents page, risk disclaimer or historical disclosure.
- Excerpts carry text hashes, topic, pending-review status and the matched
  document URL/digest through intake, coverage, research and AI packets.
  They become constrained citation IDs; local validation remains required.
- Existing research and draft data are not rewritten. Richer evidence arrives
  after the next successful content collection; failures preserve prior data.

## Schedule controls

`config/pulse-ai-policy.json` contains explicit UTC YYYY-MM active months.
An empty list disables scheduled paid analysis. Manual owner-approved trials
are independent of the schedule policy.

A free admission job reads the current pulse-data queue and cost ledger before
requesting environment approval. Inactive months, an empty/superseded queue or
$9 recorded+reserved usage skip scheduled analysis. Admission is repeated after
approval, before reservation. The existing exact-run owner approval, protected
main/CI gate and commit-before-request budget hold remain mandatory.

The $1 call estimate and $9 start threshold/$10 planning budget still apply.
$5/$8/$9 notices appear in the GitHub admission summary and public settings when
that ledger is published. These are not push/email notifications or provider
hard billing limits.

## Remaining before unattended production use

1. Independently reconcile the first SMCI draft's fiscal periods, values,
   units, cash-flow bridge, debt and legal claims with original disclosures.
2. Specify active months through a reviewed policy change, then test admission
   with a free run and verify public settings reflect published ledger usage.
3. Full unattended paid generation still requires a separately designed and
   explicitly authorized owner preauthorization policy. Setting both YES flags
   does not bypass the pulse-ai-paid required reviewer or exact-run approval.
4. Preserve a separate owner approval for publication, valuation changes and
   scenario probability changes. Missing valuation models must be built from
   reviewed assumptions; they are not fabricated by increasing scan volume.
5. Any live paid trial needs its own authorization; no model request was made
   as part of this implementation.
