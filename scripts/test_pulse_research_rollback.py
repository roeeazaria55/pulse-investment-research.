"""Rollback is a review-only pointer proposal; immutable versions cannot be lost."""
import unittest
from pulse_research_rollback import propose_rollback
from pulse_research_release import canonical,sha,validate_current_approved

CID="us-meta-nasdaq-a"
T1="research-v:"+"a"*32
T2="research-v:"+"b"*32
T3="research-v:"+"c"*32
NOW="2026-10-29T15:00:00Z"

def version(ident,parent):
 v={"id":ident,"companyId":CID,"pdfPath":"public/approved-research/META/"+ident[11:]+".pdf",
    "pdfSha256":"d"*64,"parentVersionId":parent}
 v["immutableSha256"]=sha(canonical(v).encode())
 return v
class ProtectedRollbackTests(unittest.TestCase):
 def store(self):
  return {"version":1,"versions":[version(T1,None),version(T2,T1)],
          "activeByCompany":{CID:T2}}
 def test_one_step_and_older_pdf_are_untouched(self):
  original=self.store()
  updated,event=propose_rollback(original,CID,T1,NOW)
  self.assertEqual(updated["activeByCompany"][CID],T1)
  self.assertEqual(updated["versions"],original["versions"])
  self.assertEqual(original["activeByCompany"][CID],T2)
  self.assertEqual(event["eventType"],"rollback-awaiting-owner-pr-merge")
  validate_current_approved(updated)
 def test_no_unlinked_or_cross_company_rollback(self):
  for cid,target in ((CID,T3),("other-company",T1),(CID,T2)):
   with self.assertRaises(ValueError):
    propose_rollback(self.store(),cid,target,NOW)
 def test_no_history_tamper_or_cycles(self):
  state=self.store();state["versions"][0]["pdfSha256"]="wrong"
  with self.assertRaises(ValueError):
   propose_rollback(state,CID,T1,NOW)
 def test_requires_timezone_aware_audit(self):
  with self.assertRaises(ValueError):
   propose_rollback(self.store(),CID,T1,"2026-10-29T15:00:00")
if __name__=="__main__":unittest.main()
