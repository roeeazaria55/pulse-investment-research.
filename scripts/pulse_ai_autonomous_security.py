"""Standing owner-reviewed monthly policy authorizes draft generation only.

The credential must be in a separate main-only GitHub environment. Publication
continues to use the original exact-run owner-review gate.
"""
import datetime as dt
import json
import os
import re
from pathlib import Path
from pulse_release_security import (GitHubReader,collect_evidence,verify_branch,require,
                                    is_owner,REPO,OWNER,AI_ENV)
from pulse_ai_schedule import admission
ENVIRONMENT='pulse-ai-drafts'
POLICY=Path(__file__).resolve().parent.parent/'config/pulse-ai-policy.json'

def verify_worker_environment(env,branches):
 require(isinstance(env,dict) and env.get('name')==ENVIRONMENT,'Automatic draft environment absent')
 require(env.get('deployment_branch_policy')=={'protected_branches':False,'custom_branch_policies':True},'Draft environment must select main explicitly')
 require(isinstance(branches,dict) and branches.get('total_count')==1,'Draft environment must permit exactly one branch')
 policies=branches.get('branch_policies',[])
 require(len(policies)==1 and policies[0].get('name')=='main' and policies[0].get('type')=='branch','Only main may access draft credentials')
 require(env.get('protection_rules')==[],'Unexpected draft-environment approval or external rule')

def verify_policy(policy,now):
 require(policy.get('scheduledAuthorization')=='automatic-drafts','Standing draft permission is disabled')
 result=admission(policy,{'jobs':[{'id':'policy','companyId':'policy','status':'queued'}],
                           'latestByCompany':{'policy':'policy'}},now)
 require(result['eligible'],'No owner-authorized active month')
 return result['month']

def verify_run(run,run_id,sha):
 require(run.get('id')==run_id and (run.get('repository') or {}).get('full_name')==REPO,'Foreign worker run')
 require(run.get('head_branch')=='main' and run.get('head_sha')==sha and run.get('run_attempt')==1,'Current protected main and fresh run required')
 require(run.get('status')=='in_progress' and run.get('path')=='.github/workflows/ai-automation.yml' and run.get('event')=='schedule','Only scheduled draft worker is authorized')
 require(is_owner(run.get('actor')) and is_owner(run.get('triggering_actor')),'Owner scheduler required')

def main():
 require(os.getenv('GITHUB_REPOSITORY')==REPO and os.getenv('GITHUB_REPOSITORY_OWNER')==OWNER,'Wrong repository')
 require(os.getenv('GITHUB_REF')=='refs/heads/main' and os.getenv('GITHUB_REF_PROTECTED')=='true' and os.getenv('GITHUB_RUN_ATTEMPT')=='1','Protected main context required')
 require(os.getenv('PAID_AI_ENABLED')=='YES' and os.getenv('PAID_AI_SCHEDULE_ENABLED')=='YES','Owner activation switches required')
 month=verify_policy(json.loads(POLICY.read_text()),dt.datetime.now(dt.timezone.utc).isoformat())
 api=GitHubReader(os.getenv('GITHUB_TOKEN',''))
 # Retain the original release/paid approval environment and main/owner-merged CI checks.
 evidence=collect_evidence(api,AI_ENV)
 sha=os.getenv('GITHUB_SHA');require(sha==evidence['mainSha'],'Protected main changed')
 env=api.get('/environments/'+ENVIRONMENT)
 verify_worker_environment(env,api.get('/environments/'+ENVIRONMENT+'/deployment-branch-policies'))
 run_id=os.getenv('GITHUB_RUN_ID','');require(run_id.isdigit(),'Missing run ID')
 verify_run(api.get('/actions/runs/'+run_id),int(run_id),sha)
 require(verify_branch(api.get('/branches/main'))==sha,'main changed during authorization')
 print(json.dumps({**evidence,'credentialEnvironment':ENVIRONMENT,'authorizedMonth':month,
                   'status':'standing-policy-draft-only','publicationAuthorized':False,'automaticRetryAuthorized':False}))
if __name__=='__main__':main()
