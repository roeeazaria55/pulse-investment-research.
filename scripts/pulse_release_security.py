"""Read-only GitHub evidence gate for a single-owner repository.

GITHUB_TOKEN cannot read the Administration-only branch-protection endpoint.
Instead, verify protected-main metadata (including CI enforcement on admins),
an actual owner-merged PR with successful CI, and GitHub's approval record for
THIS run and environment. Native PR/force-push/deletion rules remain configured
in GitHub; this is an outcome-based gate, not a full admin-settings audit.
No PAT, constant-true fallback, local approval JSON or model output is trusted.
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.request

REPO = "roeeazaria55/pulse-investment-research."
OWNER = "roeeazaria55"
OWNER_ID = 240902876
ACTIONS_APP_ID = 15368
RELEASE_ENV = "pulse-research-release"
AI_ENV = "pulse-ai-paid"
RELEASE_PATHS = {
    ".github/workflows/research-release-proposal.yml",
    ".github/workflows/research-final-publication.yml",
    ".github/workflows/research-rollback.yml",
}


class ReleaseProtectionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReleaseProtectionError(message)


def is_owner(user):
    return (isinstance(user, dict) and user.get("login") == OWNER
            and user.get("id") == OWNER_ID and user.get("type") == "User")


def verify_branch(branch):
    require(isinstance(branch, dict) and branch.get("name") == "main"
            and branch.get("protected") is True, "main is not protected")
    checks = (branch.get("protection") or {}).get("required_status_checks") or {}
    require(checks.get("enforcement_level") == "everyone",
            "CI enforcement must include administrators")
    require(any(c.get("context") == "check" and c.get("app_id") == ACTIONS_APP_ID
                for c in checks.get("checks", []) if isinstance(c, dict)),
            "Required GitHub Actions check missing or not app-bound")
    sha = (branch.get("commit") or {}).get("sha", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "main SHA missing")
    return sha


def verify_environment(environment, name, branch_policies=None):
    require(isinstance(environment, dict) and environment.get("name") == name
            and type(environment.get("id")) is int, "Protected environment absent")
    require(environment.get("can_admins_bypass") is False,
            "Environment admin bypass must be disabled")
    gates = [r for r in environment.get("protection_rules", [])
             if isinstance(r, dict) and r.get("type") == "required_reviewers"]
    require(len(gates) == 1, "Exactly one owner-review gate required")
    reviewers = gates[0].get("reviewers", [])
    require(len(reviewers) == 1 and reviewers[0].get("type") == "User"
            and is_owner(reviewers[0].get("reviewer")),
            "Only the repository owner may approve this environment")
    require(gates[0].get("prevent_self_review") is False,
            "Single-owner environment must allow owner-initiated runs")
    policy = environment.get("deployment_branch_policy") or {}
    if name == RELEASE_ENV:
        require(policy.get("protected_branches") is True
                and policy.get("custom_branch_policies") is False,
                "Release environment must allow protected branches only")
    else:
        require(name == AI_ENV and policy.get("protected_branches") is False
                and policy.get("custom_branch_policies") is True,
                "AI environment must use an exact main branch policy")
        require(isinstance(branch_policies, list) and len(branch_policies) == 1
                and branch_policies[0].get("name") == "main"
                and branch_policies[0].get("type") == "branch",
                "AI environment must allow main only, with no tags")
    return environment["id"]


def verify_merged_pr(pr, main_sha):
    require(isinstance(pr, dict) and pr.get("merged") is True
            and pr.get("state") == "closed" and pr.get("draft") is False
            and pr.get("merge_commit_sha") == main_sha,
            "Current main must be the exact result of a merged PR")
    require(is_owner(pr.get("merged_by")), "main PR must be merged by the owner")
    require((pr.get("base") or {}).get("ref") == "main"
            and ((pr.get("base") or {}).get("repo") or {}).get("full_name") == REPO,
            "Merged PR targets a different repository or branch")
    sha = (pr.get("head") or {}).get("sha", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "Merged PR head missing")
    return sha


def verify_ci(checks, ci_run, head_sha):
    require(isinstance(checks, list), "CI check records missing")
    candidates = [c for c in checks if c.get("name") == "check"
                  and (c.get("app") or {}).get("id") == ACTIONS_APP_ID]
    require(bool(candidates), "GitHub Actions check missing")
    check = max(candidates, key=lambda c: c.get("id", 0))
    require(check.get("head_sha") == head_sha and check.get("status") == "completed"
            and check.get("conclusion") == "success", "Latest required check has not passed")
    require(isinstance(ci_run, dict) and ci_run.get("path") == ".github/workflows/check.yml"
            and ci_run.get("event") == "pull_request"
            and ci_run.get("head_sha") == head_sha
            and ci_run.get("status") == "completed" and ci_run.get("conclusion") == "success"
            and (ci_run.get("repository") or {}).get("full_name") == REPO,
            "Check is not successful PR CI for the merged head")
    expected = f"https://github.com/{REPO}/actions/runs/{ci_run.get('id')}/job/"
    require(str(check.get("details_url", "")).startswith(expected),
            "CI check and workflow run are not bound")


def verify_run_approval(run, approvals, *, run_id, sha, environment, env_id):
    require(isinstance(run, dict) and run.get("id") == run_id
            and (run.get("repository") or {}).get("full_name") == REPO
            and run.get("head_branch") == "main" and run.get("head_sha") == sha
            and run.get("status") == "in_progress", "Run is not executing current main")
    # The approvals endpoint is per run, not per attempt. Reject reruns rather
    # than accidentally reusing a previous attempt's approval.
    require(run.get("run_attempt") == 1, "Start a fresh run; approval cannot be replayed on reruns")
    paths = RELEASE_PATHS if environment == RELEASE_ENV else {".github/workflows/ai-automation.yml"}
    events = {"workflow_dispatch"} if environment == RELEASE_ENV else {"workflow_dispatch", "schedule"}
    require(run.get("path") in paths and run.get("event") in events,
            "Untrusted workflow path or trigger")
    require(is_owner(run.get("actor")) and is_owner(run.get("triggering_actor")),
            "Only the owner may initiate this operation")
    require(isinstance(approvals, list), "GitHub approval history unreadable")
    matching = [r for r in approvals if any(
        e.get("name") == environment and e.get("id") == env_id
        for e in r.get("environments", []) if isinstance(e, dict))]
    require(bool(matching) and all(r.get("state") == "approved" and is_owner(r.get("user"))
                                  for r in matching),
            "No unambiguous owner approval for this run and environment")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ReleaseProtectionError("GitHub API redirect refused")


class GitHubReader:
    def __init__(self, token):
        require(isinstance(token, str) and len(token) >= 10, "Trusted GITHUB_TOKEN missing")
        self.token = token

    def get(self, path):
        require(path.startswith("/") and ".." not in path and not path.startswith("//"),
                "Unsafe GitHub API path")
        request = urllib.request.Request("https://api.github.com/repos/" + REPO + path, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PULSE-read-only-security-evidence",
        })
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
                data = json.load(response)
                require('rel="next"' not in response.headers.get("Link", ""),
                        "Incomplete GitHub evidence; pagination requires review")
                return data
        except (urllib.error.URLError, ValueError) as error:
            if isinstance(error, ReleaseProtectionError):
                raise
            # Never include credentials, response body, or request headers.
            raise ReleaseProtectionError("GitHub evidence API unavailable; operation blocked") from None


def collect_evidence(api, environment):
    branch = api.get("/branches/main")
    sha = verify_branch(branch)
    env = api.get("/environments/" + environment)
    policies = None
    if environment == AI_ENV:
        payload = api.get("/environments/" + environment + "/deployment-branch-policies?per_page=100")
        policies = payload.get("branch_policies")
        require(payload.get("total_count") == len(policies or []), "Incomplete branch policy list")
    env_id = verify_environment(env, environment, policies)
    candidates = api.get(f"/commits/{sha}/pulls?per_page=100")
    require(isinstance(candidates, list), "Merged PR evidence unreadable")
    matches = [p for p in candidates if p.get("merge_commit_sha") == sha
               and (p.get("base") or {}).get("ref") == "main"]
    require(len(matches) == 1 and type(matches[0].get("number")) is int,
            "Current main has no unique merged PR")
    pr = api.get(f"/pulls/{matches[0]['number']}")
    head = verify_merged_pr(pr, sha)
    checks = api.get(f"/commits/{head}/check-runs?check_name=check&filter=latest&per_page=100")
    records = checks.get("check_runs", [])
    require(checks.get("total_count") == len(records), "Incomplete CI evidence")
    matching = [c for c in records if c.get("name") == "check"
                and (c.get("app") or {}).get("id") == ACTIONS_APP_ID]
    require(bool(matching), "Required CI evidence absent")
    latest = max(matching, key=lambda c: c.get("id", 0))
    match = re.fullmatch(re.escape(f"https://github.com/{REPO}/actions/runs/")
                         + r"([0-9]+)/job/[0-9]+", latest.get("details_url", ""))
    require(match is not None, "CI provenance URL invalid")
    ci = api.get("/actions/runs/" + match.group(1))
    verify_ci(records, ci, head)
    return {"mainSha": sha, "mergedPr": pr["number"], "ciRun": ci["id"],
            "environment": environment, "environmentId": env_id}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", choices=[RELEASE_ENV, AI_ENV], default=RELEASE_ENV)
    parser.add_argument("--preflight", action="store_true", help="Read-only evidence; NEVER authorizes writes or spend")
    args = parser.parse_args(argv)
    require(os.getenv("GITHUB_REPOSITORY") == REPO
            and os.getenv("GITHUB_REPOSITORY_OWNER") == OWNER, "Repository owner mismatch")
    if not args.preflight:
        switch = "RESEARCH_RELEASE_PROPOSALS_ENABLED" if args.environment == RELEASE_ENV else "PAID_AI_ENABLED"
        require(os.getenv(switch) == "YES", "Owner has not enabled this operation")
        require(os.getenv("GITHUB_REF") == "refs/heads/main"
                and os.getenv("GITHUB_REF_PROTECTED") == "true", "Protected main context required")
        require(os.getenv("GITHUB_RUN_ATTEMPT") == "1", "Fresh run required")
    api = GitHubReader(os.getenv("GITHUB_TOKEN", ""))
    evidence = collect_evidence(api, args.environment)
    if args.preflight:
        # In CI also prove that read-only token access to review history works.
        # This branch never returns an authorization, even on an approved run.
        run_id = os.getenv("GITHUB_RUN_ID", "")
        review_history_readable = False
        if run_id:
            require(run_id.isdigit(), "Run ID invalid")
            run = api.get("/actions/runs/" + run_id)
            history = api.get("/actions/runs/" + run_id + "/approvals")
            require(run.get("id") == int(run_id) and isinstance(history, list),
                    "Current run review history unreadable")
            review_history_readable = True
        print(json.dumps({**evidence, "status": "preflight-only-not-authorized", "authorized": False,
                          "reviewHistoryReadable": review_history_readable,
                          "paidAiExecuted": False, "publicationExecuted": False}))
        return
    sha = os.getenv("GITHUB_SHA")
    require(sha == evidence["mainSha"], "main changed; start a fresh run")
    run_id = os.getenv("GITHUB_RUN_ID", "")
    require(run_id.isdigit(), "Run ID missing")
    run = api.get("/actions/runs/" + run_id)
    approvals = api.get("/actions/runs/" + run_id + "/approvals")
    verify_run_approval(run, approvals, run_id=int(run_id), sha=sha,
                        environment=args.environment, env_id=evidence["environmentId"])
    # Detect a concurrent main update while evidence was collected.
    require(verify_branch(api.get("/branches/main")) == sha, "main moved during verification")
    print(json.dumps({**evidence, "status": "owner-environment-approved",
                      "humanPrMergeStillRequired": True, "independentCodeReview": False}))


if __name__ == "__main__":
    main()
