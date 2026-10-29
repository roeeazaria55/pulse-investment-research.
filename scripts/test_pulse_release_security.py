"""Authentication and branch-policy simulations are read-only and fail closed."""
import copy
import unittest
from pulse_release_security import verify_release_protections,ReleaseProtectionError

OWNER="roeeazaria55"
REPO=OWNER+"/pulse-investment-research."
BRANCH={"required_pull_request_reviews":{"required_approving_review_count":1},
        "enforce_admins":{"enabled":True}}
ENV={"name":"pulse-research-release","protection_rules":[
     {"type":"required_reviewers","reviewers":[{"reviewer":{"login":OWNER,"type":"User"}}]}],
     "deployment_branch_policy":{"protected_branches":True,"custom_branch_policies":False}}

class SecurityGateTests(unittest.TestCase):
 def verify(self,prot=BRANCH,env=ENV,repo=REPO,owner=OWNER):
  return verify_release_protections(repo=repo,owner=owner,protection=prot,environment=env)
 def test_requires_authenticated_owner_protection_then_still_requires_merge(self):
  result=self.verify()
  self.assertTrue(result["humanPrMergeStillRequired"])
  self.assertEqual(result["status"],"verified-for-pr-proposal-only")
 def test_refuses_unprotected_main_missing_review_or_admin_bypass(self):
  for bad in ({},None,{"required_pull_request_reviews":{"required_approving_review_count":0}},
              {"required_pull_request_reviews":{"required_approving_review_count":1},"enforce_admins":{"enabled":False}}):
   with self.assertRaises(ReleaseProtectionError):self.verify(prot=bad)
 def test_refuses_environment_with_no_specific_owner_review(self):
  for bad in ({},None,{"name":"pulse-research-release","protection_rules":[],"deployment_branch_policy":{"protected_branches":True}},
       {"name":"pulse-research-release","protection_rules":[{"type":"required_reviewers",
        "reviewers":[{"reviewer":{"login":"other-account"}}]}],
        "deployment_branch_policy":{"protected_branches":True}}):
   with self.assertRaises(ReleaseProtectionError):self.verify(env=bad)
 def test_refuses_nonprotected_environment_branch(self):
  bad=copy.deepcopy(ENV)
  bad["deployment_branch_policy"]["protected_branches"]=False
  with self.assertRaises(ReleaseProtectionError):self.verify(env=bad)
 def test_refuses_forged_owner_or_different_repository(self):
  with self.assertRaises(ReleaseProtectionError):self.verify(repo="somewhere/other",owner=OWNER)
  with self.assertRaises(ReleaseProtectionError):self.verify(owner="other")
if __name__=="__main__":unittest.main()
