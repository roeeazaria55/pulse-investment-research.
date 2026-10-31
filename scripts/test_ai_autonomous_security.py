import copy
import unittest
from pulse_ai_autonomous_security import verify_policy,verify_run,verify_worker_environment,ENVIRONMENT
from pulse_release_security import ReleaseProtectionError,REPO,OWNER,OWNER_ID
class AutomaticDraftSecurityTests(unittest.TestCase):
 def test_policy_requires_explicit_mode_and_current_month(self):
  policy={'version':1,'activeMonths':['2026-11'],'scheduledAuthorization':'automatic-drafts'}
  self.assertEqual(verify_policy(policy,'2026-11-01T00:00:00Z'),'2026-11')
  for p,t in [({**policy,'scheduledAuthorization':'disabled'},'2026-11-01T00:00:00Z'),(policy,'2026-12-01T00:00:00Z')]:
   with self.assertRaises(ReleaseProtectionError):verify_policy(p,t)
 def test_only_main_in_separate_environment_can_access_secret(self):
  env={'name':ENVIRONMENT,'deployment_branch_policy':{'protected_branches':False,'custom_branch_policies':True},'protection_rules':[]}
  branches={'total_count':1,'branch_policies':[{'name':'main','type':'branch'}]}
  verify_worker_environment(env,branches)
  for e,b in [({**env,'name':'pulse-research-release'},branches),(env,{'total_count':1,'branch_policies':[{'name':'*','type':'branch'}]}),(env,{'total_count':2,'branch_policies':branches['branch_policies']*2}),({**env,'protection_rules':[{'type':'required_reviewers'}]},branches)]:
   with self.assertRaises(ReleaseProtectionError):verify_worker_environment(e,b)
 def test_only_fresh_owner_scheduled_draft_workflow_allowed(self):
  owner={'login':OWNER,'id':OWNER_ID,'type':'User'}
  run={'id':1,'repository':{'full_name':REPO},'head_branch':'main','head_sha':'a'*40,'run_attempt':1,'status':'in_progress','path':'.github/workflows/ai-automation.yml','event':'schedule','actor':owner,'triggering_actor':owner}
  verify_run(run,1,'a'*40)
  for key,value in [('event','workflow_dispatch'),('run_attempt',2),('path','.github/workflows/research-final-publication.yml'),('head_sha','b'*40),('actor',{'login':'attacker'})]:
   with self.subTest(key=key),self.assertRaises(ReleaseProtectionError):verify_run({**run,key:value},1,'a'*40)
 def test_automatic_gate_checks_live_evidence_and_never_grants_publication(self):
  import contextlib,io,json,os
  from unittest.mock import patch
  import pulse_ai_autonomous_security as gate
  from test_pulse_release_security import BRANCH
  branch=copy.deepcopy(BRANCH);sha=branch['commit']['sha']
  user={'login':OWNER,'id':OWNER_ID,'type':'User'}
  run={'id':1,'repository':{'full_name':REPO},'head_branch':'main','head_sha':sha,'run_attempt':1,'status':'in_progress','path':'.github/workflows/ai-automation.yml','event':'schedule','actor':user,'triggering_actor':user}
  responses={'/environments/'+ENVIRONMENT:{'name':ENVIRONMENT,'deployment_branch_policy':{'protected_branches':False,'custom_branch_policies':True},'protection_rules':[]},'/environments/'+ENVIRONMENT+'/deployment-branch-policies':{'total_count':1,'branch_policies':[{'name':'main','type':'branch'}]},'/actions/runs/1':run,'/branches/main':branch}
  context={'GITHUB_REPOSITORY':REPO,'GITHUB_REPOSITORY_OWNER':OWNER,'GITHUB_REF':'refs/heads/main','GITHUB_REF_PROTECTED':'true','GITHUB_RUN_ATTEMPT':'1','PAID_AI_ENABLED':'YES','PAID_AI_SCHEDULE_ENABLED':'YES','GITHUB_SHA':sha,'GITHUB_RUN_ID':'1','GITHUB_TOKEN':'fake-token-for-test'}
  with patch.dict(os.environ,context,clear=True),patch.object(gate,'verify_policy',return_value='2026-11'),patch.object(gate,'collect_evidence',return_value={'mainSha':sha}),patch.object(gate.GitHubReader,'get',side_effect=lambda p:responses[p]),contextlib.redirect_stdout(io.StringIO()) as out:
   gate.main()
  self.assertFalse(json.loads(out.getvalue())['publicationAuthorized'])
  for flag in ['PAID_AI_ENABLED','PAID_AI_SCHEDULE_ENABLED']:
   with patch.dict(os.environ,{**context,flag:'NO'},clear=True),patch.object(gate,'collect_evidence') as evidence:
    with self.assertRaises(ReleaseProtectionError):gate.main()
    evidence.assert_not_called()
if __name__=='__main__':unittest.main()
