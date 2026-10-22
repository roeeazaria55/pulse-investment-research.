# Phase 2C — Public state branch migration (draft, NOT deployed)

## Why this exists

GitHub currently reports **`main.protected = false`** and
`GET /repos/.../rulesets` returns an empty list. The existing scheduled
Pages workflow pushes raw collection snapshots directly to `main`, a
structure that conflicts with enforceable review policies.

This change prepares the first architectural prerequisite for protected
investment research: the scheduled publisher reads and writes ONLY
`pulse-data` for mutable `public/data` snapshots, while code and
reviewed decisions remain on `main`. GitHub Pages is still built from
`main` code, overlaid with the exact collected data snapshot.
The persisted-data and production-code commit IDs are verified separately
before publication. The `notify` workflow already consumes the actual
published feed artifact, so it does not depend on state being stored
in `main`.

This PR is deliberately **draft**. It must not be deployed before the
following explicit rollout steps.

## Activation steps (in order)

1. Complete the pending Phase 2C code PRs and confirm production currently
   deploys successfully. Freeze competing workflow edits for the rollout.
2. Create the `pulse-data` branch **from the latest `main` commit**,
   immediately before activation, so existing retained source snapshots
   are not rolled back. This branch must exist before activating the
   changed workflow: a missing branch intentionally makes the run fail.
3. Review the final diff of this workflow and CI checks. Confirm the
   publisher GITHUB_TOKEN can write `pulse-data` and that the branch
   has no protection setting that blocks the service account.
4. Merge this migration PR only with explicit approval, run
   `workflow_dispatch`, verify successful collect/persist/deploy/notify,
   source SHA and pending-review data continuity, and inspect the public
   Pages site. Verify schedule runs still work at least once.
5. Only **after the separated branch is confirmed functional**, configure
   repository branch rules on `main` in GitHub Settings → Rules →
   Rulesets (or Branches). Require PR merges, applicable status checks,
   and independently reviewed changes. Block direct pushes by writers,
   including automated workflows. Validate that the ruleset is marked
   **Active** and that push bypass actors are appropriately restricted.
   A one-person repository may require adding a distinct authorized
   reviewer; the author cannot simply self-approve a required
   independent PR review.
6. Verify by attempting a benign unauthorized direct push (which should
   be rejected), exercising a reviewed PR, and completing another
   scheduled `pulse-data` publication. Do not call decisions
   **Verified Analyst Approval** until the enforcement check passes.

## Security boundary and failure modes

- A GitHub PR merge while `main` is not protected does **not** constitute
  enforced approval, even if an event in JSON says `approved`.
- The review ledger in PR #27 records decisions only. Forecast comparisons
  in PR #28 remain fail-closed when verified authorization is absent.
- If the new workflow fails at rollout, revert the workflow code through
  a reviewed PR; the prior `main` snapshot remains intact.
- Do not enable main protection first: that would break the old
  scheduled direct-to-main data writer before migration.
- These changes do not modify holdings, research PDFs, prices, forecasts
  or financial models. No public client receives write credentials.
- `pulse-data` is only a state store, not an authority for valuation
  approval or financial statements.

## Access limitation

The available connected GitHub integration can **read** the ruleset list
but the branch-protection endpoint returns HTTP 403 (resource not
accessible by integration). No administrative branch rule was created
or changed in this PR. A repository administrator must apply the
settings and verify enforcement.

## Validation

Python regression test `test_public_state_branch.py` asserts the workflow
cannot push to `main`, loads the prior snapshot from `pulse-data`,
checks both revisions before deployment and still saves every financial
ingestion artifact. PR CI exercises code and mobile build; actual
live scheduled writes can be confirmed only at activation.
