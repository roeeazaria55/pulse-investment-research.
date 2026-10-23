# Phase 2C — publication workflow isolation regression tests

This draft adds `scripts/test_pipeline_isolation.py`, six read-only
standard-library Python tests for the existing GitHub Actions workflows.
They run with the repository's existing unittest discovery command.

The tests flag accidental regressions to these design invariants:

- Scheduled collection checks out **main** with read-only credentials and
  reads previous public state from `pulse-data`.
- The only Git push in the publication workflow targets `pulse-data`.
  The persist job stages an explicit allowlist of `public/data/` paths;
  neither `main` nor code/configuration files are staged.
- Deployment checks both the exact source commit and the persisted
  data-branch commit before publishing Pages.
- Notifications run after successful deployment, use the exact feed
  artifact, and retain send intents across retries.
- Pull-request CI cannot write to repository contents or use
  `pull_request_target`; workflow scripts cannot force-push `main`.

**These are regression tests, not access-control enforcement.**
The repository's `main` branch remains unprotected until an active
GitHub Ruleset, independent authorized reviewer and required checks are
configured and verified. No verified analyst approval is claimed.

This PR does not modify collection code, live sources, valuation, forecasts,
published data, notifications, or workflows. It can be reviewed independently
of draft Phase 3 PRs #31, #32 and #33.
