"""Final owner-release PR rehearsal: no API, no real research publication."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from ai_research_packets import build_all
from pulse_ai_pipeline import MockAIProvider
from pulse_ai_full_research import build_public_full_research_draft
from pulse_ai_research_drafts import append_public
from pulse_research_release import build_proposal_files,validate_current_approved
from pulse_research_publish_proposal import prepare_publication,stage_publication

NOW="2026-10-29T13:00:00+00:00"
EMPTY={"version":1,"versions":[],"activeByCompany":{}}

class TwoStepReleaseTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  packet=build_all()["DLO"]
  # Strictly local unit-test fixture. No model execution or official release.
  full=MockAIProvider().analyze(packet);full["analysisMode"]="model-generated-unverified"
  base=build_public_full_research_draft(packet,full,"gpt-6.1-sol",execution_attested=True)
  cls.draft=append_public({},base,NOW)["drafts"][0]
  cls.packet=packet
 def fixture(self,root,simulation=False):
  result=build_proposal_files(self.packet,self.draft,EMPTY,root/"stage",
                              as_of=NOW,simulation=simulation)
  path=root/"stage"/result["candidateVersion"]["pdfPath"]
  return result,path.read_bytes(),path
 def test_release_requires_independent_protected_merge_and_previous_version_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);proposal,pdf,pdfpath=self.fixture(root)
   next_index,version=prepare_publication(proposal,EMPTY,pdf)
   self.assertEqual(version["publicationStatus"],"approved-upon-protected-pr-merge")
   self.assertEqual(next_index["activeByCompany"][self.packet["companyId"]],version["id"])
   self.assertEqual(len(next_index["versions"]),1)
   self.assertFalse(version["approvedTargetChanged"])
   self.assertFalse(version["approvedScenarioWeightsChanged"])
   self.assertEqual(version["approvalTimestamp"],None)
   validate_current_approved(next_index)
   proposal_file=root/"stage/release-proposal.json"
   result=stage_publication(proposal_path=proposal_file,
       approved_path=root/"current-versions.json",pdf_path=pdfpath,outdir=root/"pending-merge-pr")
   self.assertTrue(result["approvedPointerChangeIsStillPendingPRMerge"])
   self.assertTrue((root/"pending-merge-pr"/version["pdfPath"]).exists())
   self.assertTrue((root/"pending-merge-pr/public/data/approved-research-versions.json").exists())
   with self.assertRaisesRegex(ValueError,"already exists|empty"):
    stage_publication(proposal_path=proposal_file,
       approved_path=root/"current-versions.json",pdf_path=pdfpath,outdir=root/"pending-merge-pr")
 def test_mock_cannot_be_promoted_to_actual_active_release(self):
  with tempfile.TemporaryDirectory() as d:
   result,pdf,_=self.fixture(Path(d),simulation=True)
   with self.assertRaisesRegex(ValueError,"mock"):
    prepare_publication(result,EMPTY,pdf)
 def test_changed_pdf_or_unreviewed_target_cannot_advance(self):
  with tempfile.TemporaryDirectory() as d:
   result,pdf,_=self.fixture(Path(d))
   with self.assertRaisesRegex(ValueError,"PDF"):
    prepare_publication(result,EMPTY,pdf+b"altered")
   forged=copy.deepcopy(result);forged["candidateVersion"]["approvedTargetChanged"]=True
   with self.assertRaisesRegex(ValueError,"edited"):
    prepare_publication(forged,EMPTY,pdf)
 def test_conflicting_active_pointer_and_duplicate_version_are_refused(self):
  with tempfile.TemporaryDirectory() as d:
   result,pdf,_=self.fixture(Path(d))
   approved={"version":1,"versions":[],"activeByCompany":{self.packet["companyId"]:"other"}}
   with self.assertRaises(ValueError):
    prepare_publication(result,approved,pdf)
   first,version=prepare_publication(result,EMPTY,pdf)
   with self.assertRaisesRegex(ValueError,"changed|Already published"):
    prepare_publication(result,first,pdf)
if __name__=="__main__":unittest.main()
