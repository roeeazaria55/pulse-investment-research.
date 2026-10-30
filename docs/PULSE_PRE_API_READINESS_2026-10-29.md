# PULSE — Pre-API Readiness Gate (2026-10-29)

## Security configuration update — 2026-10-29

The historical owner-setup checklist below is superseded by
[PULSE_GITHUB_SECURITY_2026-10-29.md](PULSE_GITHUB_SECURITY_2026-10-29.md).
Main and both environments are configured. One external PR review is NOT
required: this repository has only one writer. Owner environment approval
is explicit operational consent, not independent code review. The new
evidence gate uses read-only GITHUB_TOKEN endpoints, not Administration access.
Paid operation remains disabled; PR #64 remains unmerged and Draft.

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


## Final Release Readiness & Premium Polish Sprint — implementation notes

These changes are **proposed only on PR #64** and have not changed
the live site, company models or old approved PDFs.

### Hardened, owner-reviewed PDF proposal stage

- New `scripts/pulse_research_release.py` validates the archived draft's
  immutable SHA, checks its source-packet SHA and every evidence citation
  against a freshly constructed issuer packet, verifies previous approved
  version metadata (if present), and creates a collision-resistant
  `research-v:<digest>` ID.
- Renders source-cited Hebrew PDF pages locally with ReportLab, DejaVu
  Unicode fonts and bidi handling; fails closed without fonts or when a
  version already exists. PDFs are created in a private staging directory
  rather than overwriting `public/research/*.pdf`.
- A clearly marked `TEST/MOCK` PDF is built for META from the offline
  source-bound ten-section mock, explicitly **not an AI model result**.
- `research-release-proposal.yml` can open a **Draft PR** containing the
  immutable source-bound PDF and review proposal. It cannot approve, merge,
  change an active research pointer, or mutate valuation weights.
- `scripts/pulse_release_security.py` fails closed until a GitHub
  authenticated API request verifies **main branch protection** (at least
  one required PR approval, administrator enforcement) AND the
  `pulse-research-release` Environment requires the repository owner as
  reviewer and protected-branches-only deployment.
- The release workflow has a separate owner-controlled
  `RESEARCH_RELEASE_PROPOSALS_ENABLED=YES` gate. It does not depend on
  or request the OpenAI API key. It cannot run from an untrusted PR.
- **Important outstanding:** a draft release proposal PR being approved
  or merged is **not itself** an update to the official active research
  pointer. The separately secured final publication, archived active
  version migration, rollback and PDF linkage are still required. No
  accepted model changes should be inferred from a proposed PDF.

### Responses API contract verification

The official OpenAI documentation describes `text.format` for JSON Schema,
`strict: true` requiring closed objects and all properties marked
required; incomplete and refused responses must be handled separately.

`scripts/pulse_responses_schema.py` now generates that strict provider
schema without deleting the local business validator. The private
executor rejects refusal, incomplete, invalid JSON, source-invalid and
mock-labeled responses. The first real billable request is **still blocked**
until the owner configures provider billing and secrets.

Sources:
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/reference/resources/responses/methods/create

### Premium application and visual acceptance

- The Research report now displays an explicit **Current vs Proposed**
  table for each company with an existing quantitated model, including
  scenario-specific probabilities. It does not alter or imply approval of
  the stored model.
- The PR CI now creates screenshots of all five mobile screens and
  desktop routes, plus dark/light Settings, via
  `scripts/pulse_visual_review.py`. These screenshots are ephemeral
  `pr-mobile-evidence` artifacts, not production assets.
- `scripts/pulse_mock_research_pdf.py` produces an offline PDF from
  the actual retained META Q3 issuer packet and the mock analyst schema.
  The PDF is explicitly TEST/MOCK and cannot update approved research.

### Required manual GitHub configuration (owner action)

**Before attempting any release proposal PR:**

1. Open GitHub repository **Settings → Rules → Rulesets** (or Branches,
   depending on the available UI). Configure a branch protection rule for
   `main` with at least one required PR review, including administrator
   enforcement. Confirm the policy appears in authenticated REST data.
   Branch rules must not unintentionally prevent the separate audited
   `pulse-data` collection workflow.
2. Under **Settings → Environments**, create
   `pulse-research-release`. Configure **Required reviewers** to the
   repository owner account and restrict deployment to protected branches.
   Ensure the required reviewer policy is genuinely available/enforced on
   the account plan; if unsupported, **release stays blocked**.
3. Under **Settings → Actions → General**, verify that workflows have
   minimal default permissions, and allow explicit scoped pull-request
   creation only if GitHub requires it for the new protected proposal job.
4. Leave repository variable
   `RESEARCH_RELEASE_PROPOSALS_ENABLED` **unset or NO** until those
   protections are verified. Then allow one reviewed proposal dispatch
   from `main` for a specific immutable draft ID. Inspect the created
   Draft PR before any merge.
5. Keep `PAID_AI_ENABLED` **NO** and do not add `OPENAI_API_KEY` until
   the actual pre-API security review is complete.

### Current release status

**Not an API activation GO.** Verified source acquisition, mock research,
PDF proposal code, authentication checks and UI regressions make the project
closer to readiness, but owner-configured GitHub protection, a fully
authenticated official publication/rollback path, physical Android validation
and paid model availability/quality remain blockers. Passing unit tests alone
does not remove them.


## Two protected GitHub PRs and explicit rollback (final polish)

The research publication protocol now has **two independent owner-reviewed
PRs**. This is a deliberate audit/security boundary, not an anonymous public
web approval button:

1. **Review PDF proposal:** Owner enables protected release environment and
   launches `research-release-proposal.yml` from protected `main` with
   `ticker` and the exact immutable `ai-draft:` ID. The guarded workflow
   verifies owner and branch protections through GitHub's authenticated API,
   checks the source-bound packet and PDF hashes, and opens a **Draft PR**
   with PDF under `public/research-release-proposals/`, *not* the approved
   research directory. Human review and merge place only the proposal on main.
2. **Final version publication:** The owner separately launches
   `research-final-publication.yml` with the previously merged proposal
   version digest. It checks source PDF SHA, parent version ancestry and
   existing index, then opens a **second Draft PR**. This PR changes the
   `approved-research-versions.json` pointer and adds an immutable PDF
   under `public/approved-research/`. **Only a protected human GitHub
   review/merge makes that new pointer active.** It never rewrites
   `src/data/models/*.json` or original `public/research/*.pdf`.
3. **Protected rollback:** `research-rollback.yml` prepares a third type
   of review PR which moves the active pointer only to a proven ancestor
   version, with an immutable audit event. All PDF bytes and historical
   version records remain untouched.
4. **Read-only app:** `ApprovedResearchHistory.tsx` exposes the new
   version history and PDFs if the approved index exists, and safely
   displays an empty state otherwise. The app cannot itself approve,
   restore or publish research.

These workflows are committed only on **Draft PR #64**; GitHub Actions
`workflow_dispatch` will not offer them on protected `main` until
the user explicitly approves a merge. They also cannot operate unless
`RESEARCH_RELEASE_PROPOSALS_ENABLED=YES`, owner-reviewed
`pulse-research-release` Environment and enforce-admins branch protection
are actually configured. If GitHub API access or protection state is
missing, the workflows fail closed.

**Important distinction:** this releases a source-backed research PDF and
its archive pointer. It intentionally does **not** automatically
adopt any new valuation assumptions, scenario weights or price targets in
the existing canonical company model. Those require separately reviewed
model edits and regression tests. Do not conflate a published AI research
document with an approved changed valuation.

### End-to-end evidence and screenshots

PR CI now creates a reproducible, explicitly labelled
`META Q3 2026 TEST/MOCK` Hebrew PDF and generates actual Chromium
screenshots for Home, Portfolio, News, Research, Watchlist, and Settings
in light mode for 390px mobile and desktop. These are the PR preview
(`pr-mobile-evidence` and `pr-report-intake-evidence` artifacts), not
proof of production deployment or physical Android compatibility.

The protected environment/ruleset and paid OpenAI model execution cannot
be made real by a mock test. **Keep the API Key disconnected until
owner-configured GitHub protection and this release review are complete.**
