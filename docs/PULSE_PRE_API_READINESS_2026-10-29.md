# PULSE — Pre-API Readiness Gate (2026-10-29)

## Release decision

**No-Go for activating a real paid API key or merging into main until the remaining
security and publication gates are verified.** All work lives on PR #64, draft.
The production website and approved investment research were not modified
by this branch.

This document distinguishes code already committed, offline simulation and
behaviour requiring external owner configuration. No API charges were made.

## Verified existing baseline

- Source-bound earnings-research candidates, previous revision history and
  read-only research evidence are already on the PR #64 branch.
- Official META Q3 2026 report and five financial metrics were detected in
  `pulse-data/public/data/latest-research-updates.json`; this is a pending,
  unapproved source snapshot, **not** proof of model interpretation.
- Before this sprint, branch CI passed 271 Python tests, 260 Vitest tests,
  TypeScript, build, mobile and PDF/PWA checks. This sprint adds more tests,
  and its **latest head CI must be independently checked**.

## Pre-API work implemented in this sprint

| Capability | Current state | Proof / limitations |
| --- | --- | --- |
| Source-triggered AI queue | **Implemented on branch** | `scripts/pulse_ai_analysis_queue.py` derives a unique job from candidate/source digest. Queued/blocked jobs and all history are persisted to `pulse-data` through the existing scheduled collector after merge. |
| Re-run safety | **Implemented on branch** | Source-digest identities, revision history and explicit state transitions; duplicate job creation is rejected. |
| Full source research packet | **Implemented, partial source coverage** | `scripts/ai_research_packets.py` includes current issuer research, history, archived forecasts and model pointers. Latest issuer-source metrics are now explicitly citable for META without falsely marking them approved. |
| Mock/real provider separation | **Implemented** | `scripts/pulse_ai_pipeline.py` performs only local, labeled mock execution. `OpenAIProvider` remains unavailable in replay. Paid model execution lives in a distinct guarded runner. |
| Full ten-section AI research contract | **Implemented** | `schemas/pulse-full-research-draft-v2.schema.json` and `pulse_ai_full_research.py` require summaries, ten cited analytical sections, unknowns and no unapproved target. Missing data must stay explicitly unquantified. |
| OpenAI Responses adapter | **Prepared, untested with a key** | `run_optional_ai_review.py` uses Responses JSON Schema, `store:false`, bounded output, citation validation and no automatic model edits. First real model response may require schema/prompt adjustments. |
| Durable budget reservation | **Implemented at code level; not live** | `pulse_ai_actions.py` and protected Actions plan persist a reservation to `pulse-data` **before** invoking API. One queued report per workflow; billed receipt is stored afterward. A failed/unknown call remains reserved, never silently retried. |
| Spending control | **Prepared, not a provider hard cap** | $10 monthly goal, prevent new calls at $9, keep $1 reserve, $1 per-request estimate cap, model price allowlist, no AI on ordinary news polling. Costs may differ from OpenAI invoices; configure provider-side budgets/alerts and reconcile. |
| GitHub Actions owner gate | **Code present; environment owner setup required** | `.github/workflows/ai-automation.yml` runs from main only, with `PAID_AI_ENABLED=YES`, environment `pulse-ai-paid` and `OPENAI_API_KEY`. Adding the key alone will NOT trigger paid analysis. |
| Human approval of official research | **Blocked on verified GitHub protections** | No active repository rulesets were returned by GitHub on 2026-10-29; branch protection was not accessible to this integration. No unverified browser button or AI JSON may approve a model. |
| Version history of drafts | **Implemented** | `pulse_ai_research_drafts.py` produces immutable, hash-linked review-only versions. Current approved target, thesis and PDF are never overwritten. |
| Approved PDF regeneration | **NOT completed** | Existing PDFs remain untouched. Versioned PDF output requires a securely approved canonical research release and visual validation for RTL and numbers. |
| Premium mobile interface | **Substantial but partial redesign** | Home intelligence, News review queue, Research report, ten-section reading UI and functional Settings modal with theme/budget. Portfolio/Watchlist receive light theme styling but need detailed final UX review. |
| Device QA | **CI automated; real device unverified** | 320/390/430 Chromium + 200% typography, PWA/PDF and browser storage checks run in PR CI. Real Android install and push notifications are not verified. |
| Paid META production test | **NOT run** | Requires owner's secret and explicit spending authorization. Mock CI path must be green before activation. |

## Architecture

```text
Existing read-only Pages collector (public)
    └── official issuer source / report intake
         └── immutable earnings candidate + SHA
              └── ai-analysis-queue.json persisted in pulse-data
                   └── protected AI workflow (OFF by default)
                        ├── verify current source packet
                        ├── pre-reserve cost -> git commit/push pulse-data
                        ├── call private Responses API (only when enabled)
                        ├── validate source citations and research v2
                        ├── record actual cost receipt or hold for reconciliation
                        └── public draft, NOT approved (pulse-data)
                             └── Pages next scheduled build displays pending review
                                  └── owner review / protected PR publication
                                      [BLOCKED until owner configures ruleset]
```

GitHub Actions uses serialized paid runs, remote source snapshots and
optimistic Git push. If the remote data branch changes before a push, the
workflow fails rather than discarding the reservation. A push failure after
a billable call leaves the source job reserved and requires human billing
reconciliation. This is safer than a silent retry but is not a transactional
external billing guarantee.

The static Pages browser never receives the API key and cannot authorize
payments or modify approved research.

## Mock rehearsal

Run after current official-source collection and packet generation:

```sh
python3 scripts/earnings_research_candidates.py
python3 scripts/pulse_ai_analysis_queue.py
python3 scripts/ai_research_packets.py
python3 scripts/pulse_ai_pipeline.py --ticker META --output work/pulse-ai-mock-preview.json
```

The file in `work/` is deliberately nonpublic, marked
`mock-simulation-no-model`, `paidAiExecuted:false` and
`publicationStatus:not-approved`. It proves source selection, queue
idempotence, contract validation and preview creation, **not** an actual
model result, an authenticated approval or live deployment.

Tests cover META/Q3 mapping, DLO and source-only issuer packets. Unrecognized
report formats remain blocked rather than invented.

## Security checks still requiring the repository owner

1. Confirm `main` and `pulse-data` write protections and role separation.
   The GitHub REST API returned no active rulesets, and this integration
   could not inspect Branch Protection. Do not trust textual approval flags.
2. Create/configure the `pulse-ai-paid` GitHub Environment and restrict
   the workflow to the protected `main` branch. Determine whether required
   reviewers should gate only initial activation vs each paid run.
3. Require an authenticated owner review and Merge for approved research
   versions. Never treat `pending-review` as approved. Protect approved
   version pointers and immutable PDF path history.
4. Create a separate OpenAI API project with billing budget and alerts; the
   app's $10 and $9 thresholds are conservative local guards, not a hard
   OpenAI billing ceiling.
5. Review source privacy before publishing derived AI text in a public repo.
   `pulse-data` and GitHub Pages are public surfaces; no personal holdings,
   private keys, private token usage logs or private documents are allowed.
6. Verify live Android PWA behavior and notification delivery before launch.

## API ACTIVATION — USER ACTION REQUIRED (LATER, NOT NOW)

After a reviewed green PR and a protected owner-approved merge:

1. On the OpenAI API platform create a project for PULSE with a spending
   budget of **up to $10 per active month**, cost alerts and provider-side
   spend controls where supported. Verify model availability and standard
   prices on the actual account.
2. Create `pulse-ai-paid` as a protected GitHub Environment, with branch
   restrictions and documented reviewer policy. Restrict Actions write
   permissions to the protected paid workflow.
3. Add `OPENAI_API_KEY` as an **Environment secret**, not into source,
   the PWA, PR comments or ChatGPT.
4. Keep `PAID_AI_ENABLED` unset/disabled initially. Run the free
   `workflow_dispatch` mode `preflight` and verify no billable requests.
5. After explicit approval, enable `PAID_AI_ENABLED=YES`, invoke
   `run-one` for **META** with no concurrent runs, verify an immutable
   reservation is committed before any paid HTTP request.
6. Compare the source hashes, output citations and numerical assertions.
   Confirm actual API usage and cost and preserve the resulting research
   as `requires-human-review` until owner approval.
7. Only then allow the scheduled AI workflow to analyze verified reports,
   one source per run. Disable `PAID_AI_ENABLED` immediately if results
   or costs are inconsistent.

## Commands / acceptance

```sh
npm ci
python3 -m unittest discover -s scripts -p 'test_*.py'
npm test
npm run typecheck
npm run validate:data
npm run build
```

Run `scripts/mobile_check.py` against the preview site after Playwright
is installed. PR CI retains real Chromium screenshots in the
`pr-mobile-evidence` Action artifact and mock JSON in
`pr-report-intake-evidence`. Do not claim Android device acceptance.

**GO for connecting an API key only when:** all tests and mobile visual
checks pass; live source collection and META mock replay are reconciled;
paid remote reservation and budget controls have been independently
reviewed; `pulse-ai-paid` environment is protected; source privacy and
official approval protections are configured.

**GO for auto-publishing new approved investment research only when:**
owner-approved GitHub rulesets, protected review/merge and immutable
PDF/versioned archive pipeline are tested separately.
