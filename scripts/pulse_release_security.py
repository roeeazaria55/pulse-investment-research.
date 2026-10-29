"""Fail-closed GitHub release gate; called only by a trusted main workflow.

No untrusted JSON, browser button or AI response can act as an approval.
Protected GitHub Environment *and* actual main branch protections must be
observable through the authenticated GitHub REST API before even proposing
a versioned PDF for merge. A release is authorized only by subsequent human
PR review and merge, never by this script.
"""
import json
import os
import urllib.error
import urllib.request
import re

class ReleaseProtectionError(ValueError):
    pass

def verify_release_protections(*,repo,owner,protection,environment):
    if not isinstance(repo,str) or not re.fullmatch(r"[\w.-]+/[\w.-]+",repo):
        raise ReleaseProtectionError("Repository identity missing")
    if repo.split("/")[0]!=owner or not re.fullmatch(r"[A-Za-z0-9-]+",str(owner)):
        raise ReleaseProtectionError("Unexpected GitHub owner")
    if not isinstance(protection,dict):
        raise ReleaseProtectionError("main branch protection must be readable and enabled")
    reviews=protection.get("required_pull_request_reviews")
    if not isinstance(reviews,dict) or int(reviews.get("required_approving_review_count") or 0)<1:
        raise ReleaseProtectionError("main requires at least one approved PR review")
    if not (protection.get("enforce_admins") or {}).get("enabled"):
        raise ReleaseProtectionError("main protection must include administrators")
    if not isinstance(environment,dict) or environment.get("name")!="pulse-research-release":
        raise ReleaseProtectionError("Protected release environment absent")
    reviewers=[]
    for rule in environment.get("protection_rules",[]):
        if rule.get("type")!="required_reviewers":
            continue
        for obj in rule.get("reviewers",[]):
            reviewer=obj.get("reviewer") or obj
            if reviewer.get("login"):reviewers.append(reviewer["login"])
    if owner not in reviewers:
        raise ReleaseProtectionError("Release environment must require owner review")
    branch_policy=environment.get("deployment_branch_policy")
    if not isinstance(branch_policy,dict) or not branch_policy.get("protected_branches"):
        raise ReleaseProtectionError("Release environment must restrict deployments to protected branches")
    return {"status":"verified-for-pr-proposal-only","humanPrMergeStillRequired":True,
            "repo":repo,"owner":owner,"protectedBranch":"main",
            "releaseEnvironment":"pulse-research-release"}

def authenticated_github_json(url,token):
    if not isinstance(token,str) or len(token)<10:raise ReleaseProtectionError("Trusted GitHub Actions token missing")
    if not url.startswith("https://api.github.com/repos/"):
        raise ReleaseProtectionError("Unsafe GitHub API endpoint")
    request=urllib.request.Request(url,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"PULSE-release-protection-read-only"
    })
    try:
        with urllib.request.urlopen(request,timeout=15) as response:
            return json.load(response)
    except (urllib.error.URLError,ValueError) as e:
        # Do not print the token, URL or unexpected server body.
        raise ReleaseProtectionError("GitHub protection API unavailable; release blocked") from None

def main():
    repo=os.environ.get("GITHUB_REPOSITORY","")
    token=os.environ.get("GITHUB_TOKEN","")
    owner=os.environ.get("GITHUB_REPOSITORY_OWNER","")
    if not repo.startswith(owner+"/") or owner!="roeeazaria55":
        raise ReleaseProtectionError("Repository owner mismatch")
    if os.environ.get("RESEARCH_RELEASE_PROPOSALS_ENABLED")!="YES":
        raise ReleaseProtectionError("Owner has not explicitly enabled release proposals")
    if os.environ.get("GITHUB_REF")!="refs/heads/main":
        raise ReleaseProtectionError("Release proposal requires protected main")
    base="https://api.github.com/repos/"+repo
    result=verify_release_protections(
      repo=repo,owner=owner,
      protection=authenticated_github_json(base+"/branches/main/protection",token),
      environment=authenticated_github_json(base+"/environments/pulse-research-release",token))
    print(json.dumps(result))
if __name__=="__main__":main()
