# PULSE GitHub security — 2026-10-29

## Saved repository settings

- `main`: require PR, required GitHub Actions `check` (app 15368), up-to-date branch, enforce administrators / no bypass; force push and deletion disabled. No additional review is required because owner `roeeazaria55` is the sole writer (zero collaborators).
- `pulse-research-release`: required reviewer owner, self-review permitted, administrator bypass disabled, protected branches only.
- `pulse-ai-paid`: same owner approval, self-review permitted, no bypass, exact `main` branch only, no tags. No API secret added.
- Actions default token: read contents/packages. GitHub bundles PR creation and approval in one repository toggle; it is enabled to permit proposal creation. Workflows never approve or merge PRs. Main requires a human merge; generated proposals remain Draft. Marking a generated draft ready triggers CI because GITHUB_TOKEN-created PRs do not trigger it automatically.
- `PAID_AI_ENABLED=NO`. `RESEARCH_RELEASE_PROPOSALS_ENABLED` remains absent/off.
- `pulse-data` has no newly imposed protection; collector workflow is unchanged.

Settings: [main](https://github.com/roeeazaria55/pulse-investment-research./settings/branch_protection_rules/85539175), [release environment](https://github.com/roeeazaria55/pulse-investment-research./settings/environments/25697260432/edit), [AI environment](https://github.com/roeeazaria55/pulse-investment-research./settings/environments/25697390891/edit), [Actions](https://github.com/roeeazaria55/pulse-investment-research./settings/actions).

## Runtime evidence and limitations

GITHUB_TOKEN cannot inspect the Administration-only branch protection endpoint. No PAT or extra account is introduced. The fail-closed gate instead checks protected-main metadata with admin-enforced app-bound CI; the exact main commit must come from an owner-merged PR whose latest required GitHub Actions check passed in `check.yml`. It also verifies the actual environment policy and GitHub approval history for the current workflow run, exact environment ID, owner, workflow, main SHA and first run attempt. Reruns are blocked to prevent approval replay; start a fresh dispatch. Main is re-read to detect concurrent changes.

This is outcome-based evidence, not a full API audit of every native branch setting. PR/force-push/deletion policies were verified in GitHub settings and are enforced there. A repository administrator can still edit settings, as with other owner-controlled repositories. Environment approval is NOT an independent second-person code review.

PR CI performs read-only preflight of both environments with the actual scoped GITHUB_TOKEN, including approval-history readability. Preflight never authorizes publication or paid calls. Missing evidence, failed CI, API failure, wrong environment, absent owner approval, bypass/self-lock settings and rerun attempts fail closed. Write permissions are limited to jobs that persist data or create proposal PRs; evidence reads use actions/checks/pull-requests read. No actions-write or admin token is used.

## Activation handoff

Code is confined to Draft PR #64. No merge, production publication, approved research/target change or paid API test was performed. After final CI review, the owner must separately authorize merging this PR before these workflows exist on main. The API key belongs only in the `pulse-ai-paid` environment as `OPENAI_API_KEY`, never in repository files or browser code. Adding that secret alone cannot activate paid calls: the owner must separately enable `PAID_AI_ENABLED=YES` and approve the environment for a fresh eligible run. Provider billing/model availability and the first real response remain untested without a key.

Research release remains off until separately enabled and approved. Its workflows create draft proposal/publication/rollback PRs; owner review, ready-for-review CI and manual merge remain separate steps. No workflow approves or merges them. Do not describe mock tests as live release or provider validation.
