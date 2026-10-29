# PULSE — Automated Earnings Research Engine (review sprint, 2026-10-28)

**Branch:** `pulse/automated-earnings-research-engine-20261028`. **PR:** #64 (Draft).  
**Safety:** zero automatic publication of analyst interpretations, scenarios, targets, holdings or PDF changes. Do not merge without authorization.

## Actual source → draft pipeline

```
GitHub Actions (existing collector, ~30 min polls)
  → official_sources → report_intake (official raw content)
  → financial_observations (proposals only)
  → issuer_coverage (latest SUPPORTABLE period, not guaranteed newest issuer release)
  → latest_research_updates / research_update_history
  → earnings_research_candidates (append-only source + period bound candidates)
  → ai_research_packets (read-only context; no paid AI call)
  → validate/build/PWA
  → pulse-data commit + Pages deployment only when CI/collection/validation succeeded
```

**Core new artifact:** `public/data/earnings-research-candidates.json`. Stable candidate IDs use the issuer, source URL, SHA-256 of retrieved bytes, published report period and source-research content ID. The artifact retains all prior candidates on future runs, flags current pointers, and is not a publication ledger. A new source version creates a separate candidate; repeat collection of the same content produces no new candidate. Once a draft is created, the record is not rewritten in a subsequent normal collection.

- Every displayable numeric row is linked to the exact issuer URL and source digest, unit and accounting period. Rejected source identity and malformed metrics fail closed.
- Comparable YoY/current-prior math requires explicit matching duration or two balance-sheet dates. DLO reconciliation blocks historical comparison; negative or zero bases have no percentage-growth claim.
- Candidate status is `needs-review` or `blocked`, with `publicationStatus=not-approved`, `modelChange=none`, `aiAnalysisExecuted=false`. It is **not** a complete analytical thesis or an AI-generated recommendation.
- Historic monitoring topics are copied as **questions/risks to review**, not evidence of a changed thesis or new target.
- The existing `Research` page displays source evidence, metric comparisons, unresolved questions and older drafts. It does not write to the browser's private research storage or publish an approved valuation.

## META Q3 2026 test scope

The source adapter in `scripts/issuer_table_adapters.py` requires:
- the registered META issuer, recognized Q3 2026 official results title, and HTML statement;
- exact GAAP unaudited consolidated income statement title, USD million units, and three-month Q3 2026/Q3 2025 columns separated from nine-month YTD columns;
- a **single** Revenue row and only one matching official statement;
- numeric current/prior values from the original statement, rather than a hardcoded $64,601 figure.

The retained GAAP statement fixture verifies Q3 2026 revenue 64,601 million USD vs Q3 2025 51,242 million USD, but **the fixture is not proof that the live collector has successfully saved or published the META source**. Live status must be checked from the actual `pulse-data` output and Pages deployment after release. Alternative report layouts remain unsupported until reviewed.

## Analyst approval and versioned publication (not yet implemented)

The public, static GitHub Pages interface is **not an authentication boundary**. An unauthenticated "Approve" button or self-declared JSON approval would violate the review contract.

To publish a full refreshed thesis **in a later approval-gated PR**:
1. Export the candidate and source packet; have the owner review PDF/original issuer text, actual accounting definitions, model sensitivity and contrary risks.
2. Create explicit, issuer-specific revised research content referencing the candidate's source digest and prior approved research version.
3. Prepare versioned research / PDF files **without overwriting existing filenames or content**. Compute and verify hashes.
4. Require GitHub repository owner approval under an enforced GitHub branch-protection/ruleset or verified review workflow before merging. Do not treat public JSON fields as authenticated approvals.
5. After the approved merge, a separate publication task updates the current-research pointer, leaving the prior versions and PDFs accessible. Verify the live published pointer equals the approved Git commit.
6. If permissions/branch-protection policies are not configured, **block publication**.

This PR deliberately does not claim a secured end-to-end human approval mechanism or automatic Bear/Base/Bull valuation update.

## Production reliability

The first deployment attempt for main commit `63c013a0b9de` failed in `scripts/mobile_check.py` when trying to parse a missing `data/ai-research-packets/<ticker>.json` as JSON. This PR explicitly regenerates read-only AI packets **before the production build**, matching the existing mobile check and PR process. Verify from the upcoming PR CI and a real main release after approval; previous failed main workflows remain unresolved until deployment succeeds.

Workflows now persist the candidate artifact to `pulse-data`, seed it on future runs and include it in production/PWA source. The main branch remains untouched by this PR.

## Test/acceptance matrix

- Python candidate suite: 12 issuers, META Q3 comparable arithmetic, DLO block, malicious source, changed SHA/new version, rerun idempotence, missing original.
- META adapter: original statement, revised reported value, wrong year/header, duplicate statement.
- Vitest UI: source-host allowlist, immutable not-approved label, no AI self-approval/automatic model change, and current-pointer integrity.
- Existing Python, Vitest, TypeScript, Vite build and Playwright mobile/PDF/offline regression suite must pass on the PR head.
- **Production acceptance** additionally requires live GitHub Actions collect/persist/deploy success, actual META source/period in `pulse-data`, real Android test for PWA claims, and secure owner review before any changed approved thesis/target is published.

## Remaining engineering backlog (not achieved by this PR)
- A verified GitHub PR-based approval publication workflow with protected actor identity and durable immutable full research version manifests.
- Full current-vs-proposed narrative and model sensitivity with company-specific dynamic Bear/Base/Bull weights; no generated prices without audited assumptions.
- Full financial statement mappings for all 12 companies (new formats require strict new adapters); no claim every newest report is currently supported.
- Proven automated end-to-end META Q3 intake from a live source and production Pages screenshot, not merely a controlled fixture.
- Automatic PDF generation on APPROVED research only, with historical PDFs retained.
- Physical Android PWA/Push acceptance and production `pulse-data` persistence proof after a successful release.

## Exact manual review procedure

Check `public/data/earnings-research-candidates.json` and `public/data/ai-research-packets/`; compare to `public/data/latest-research-updates.json`, inspect each official source URL and SHA-256. A `needs-review` draft is just a question to answer, not an approved investment conclusion. Do not merge this PR until CI and owner review are complete.

## Phase 5 — Premium UI and opt-in OpenAI API adapter (2026-10-29)

**Implemented on PR #64 (not merged):**
- Source-aware premium `AIResearchOverview` home panel. It shows real counts only if the collected public candidate JSON is available; it never claims an AI analysis ran. The monthly `$10` is a planned usage allowance, **not** a fixed fee or a current usage metric.
- Premium `AIReviewDraftPanel` research view. It reads optional `public/data/ai-research-drafts.json`, clearly marks AI work as unverified and keeps approvals/prices unchanged. The file is intentionally absent until a draft has been explicitly produced and staged.
- Existing `run_optional_ai_review.py` can preflight all 12 registry companies at zero API cost. Executing a real OpenAI Responses call now supports `gpt-6-luna` / `gpt-6.1-sol`, validated JSON Schema and the original source-bound citation contract. Output remains a private, non-overwriting local JSON file.
- `pulse_ai_cost_guard.py`: conservative USD $10 monthly budget, a $9 start-block threshold, $1 max estimate per request, durable reservations to prevent repeated calls, actual usage receipts, and explicit model price allowlist. A reserved request that fails is held for manual reconciliation rather than silently retried. This **cannot** guarantee the OpenAI invoice equals the local estimate; a provider account/project budget must be configured independently.
- `pulse_ai_research_drafts.py`: converts an externally reviewed private AI JSON output to a bounded public *draft* with cited evidence, hashed history and zero approval permissions. This is a staging tool, **not** proof that an AI run actually occurred.
- New Python and frontend tests cover budget accounting, source citations, duplicate prevention, validation of suggestions and malicious approval attempts.

### Activation sequence — user wants key only after code and review

1. Inspect PR #64 and CI. Continue to keep it in Draft. No API call is part of the public Pages collector or PR build.
2. Inspect current Standard prices in the OpenAI dashboard; adjust model prices and tests as needed. The hardcoded rates in `scripts/pulse_ai_cost_guard.py` are estimates for 2026-10-29.
3. On the OpenAI API platform, set a provider-side monthly/project budget and spend alerts. The local $10 guard is a software safety layer and is **not** a hard billing cap.
4. Only when the user approves paid execution, add `OPENAI_API_KEY` in the authorized private runner environment. Never paste it into ChatGPT, source, git diff, logs, the browser or public GitHub Actions artifacts.
5. To run the guarded CLI manually (from a private machine with retained project files), create a private budget directory **outside the repository**. Set `PULSE_PAID_AI_APPROVED=YES` explicitly, then run `python3 scripts/run_optional_ai_review.py --ticker META --execute --private-output /private/path/meta-review.json --cost-ledger /private/path/ai-costs.json`. A successful call returns only status, source hashes, evidence counts, token-derived cost and a private JSON result.
6. After external inspection of source evidence and no-private-content policy, use `pulse_ai_research_drafts.py` to stage a public review-only feed. This action cannot approve prices, weights, PDF research or portfolio positions.

### Outstanding blockers for fully automatic premium research

- **No paid API calls have been executed or authorized**. The user must configure the secret and authorize the first call.
- A reliable scheduled runner with an enforced central $10 provider-side budget and persistent transactional billing ledger is **not yet connected**. The current guarded executor is opt-in/manual; simply adding the key does not start paid analysis.
- AI drafts are not yet automatically pushed to `pulse-data` or promoted into a current-versus-proposed analyst-approved publication. A source-safe, authenticated publication workflow still needs branch rules and separate approval.
- UI polish has been applied to the Home intelligence card and research review panels; this is **not** a complete replacement of all five application screens, light-mode support or physical Android/PWA acceptance.
- No revised META price target or probability weights were generated. Existing approved research remains untouched.

### Offline test gates

`python3 -m unittest discover -s scripts -p 'test_*.py'`, `npm test`,
`npm run typecheck`, `npm run validate:data`, `npm run build` and the existing Playwright checks must pass before release.

## Final Pre-API Sprint — reproducible status (2026-10-29)

**Read first:** [PULSE Pre-API Readiness Gate](PULSE_PRE_API_READINESS_2026-10-29.md).
That matrix lists source-based checks, activation instructions, actual owner
configuration blockers and exact Go/No-Go. PR #64 remains unmerged.

Changes since the initial review-only prototype:
- Source-derived `ai-analysis-queue.json` is part of `pulse-data`
  ingestion and persistence; revisions produce new task IDs without
  approving or overwriting previous research.
- `MockAIProvider` runs a **ten-section source-cited v2 report** without
  any OpenAI call or invented price. Retained META Q3 2026 issuer metrics
  are now citable with `issuer-report-metric` IDs and period/source digest.
- The `ai-automation.yml` workflow is gated by the protected branch,
  explicit `PAID_AI_ENABLED=YES`, the owner-managed `pulse-ai-paid`
  environment and `OPENAI_API_KEY`. Before any future billable call, a
  cost reservation and job transition must be pushed to `pulse-data`.
  A missing receipt or write conflict blocks automatic retry.
- Ten-section `pulse-full-research-draft-v2.schema.json` and
  `pulse_ai_full_research.py` validate report structure, citations,
  uncertainty, and no automatic target or portfolio changes.
- Research, News and Home expose evidence/queue status. A functional
  Settings dialog stores dark/light preference locally and shows current
  usage and reservation information only when the read-only ledger exists.
- The `pulse-data` cost ledger is read-only in Pages; no frontend API
  key, mutable owner approvals or invented telemetry.
- Exact physical Android install, owner-configured branch protection,
  versioned **approved** PDF publication, and real model quality/cost
  verification remain uncompleted. No paid API use in this sprint.

Current data and source code on this Draft PR are **not** live on the
public site until an owner-approved main release.
