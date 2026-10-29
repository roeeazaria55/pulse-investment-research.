"""Release proposal/PDF tests: no real model, no approval, no existing files edited."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from ai_research_packets import build_all
from pulse_ai_pipeline import MockAIProvider
from pulse_ai_full_research import build_public_full_research_draft
from pulse_ai_research_drafts import append_public
from pulse_research_release import (
 build_proposal_files,pack_version,validate_current_approved,
 validate_unapproved_source,sha,SAFE_ROOT
)

NOW="2026-10-29T14:00:00+00:00"
EMPTY={"version":1,"versions":[],"activeByCompany":{}}

class ReleasePreviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packet=build_all()["DLO"]
  raw=MockAIProvider().analyze(cls.packet)
  # Test-only forged model output exercises the real release proposal
  # validation pipeline. The artifact is *always* tagged simulation=True.
  raw["analysisMode"]="model-generated-unverified"
  draft=build_public_full_research_draft(cls.packet,raw,"gpt-6.1-sol",execution_attested=True)
  cls.draft=append_public({},draft,NOW)["drafts"][0]
 def test_immutable_archive_validation_and_no_target_promotion(self):
  full=validate_unapproved_source(self.draft,self.packet)
  self.assertEqual(len(full["sections"]),10)
  section,version=pack_version(self.packet,self.draft,EMPTY,as_of=NOW)
  self.assertEqual(version["publicationStatus"],"proposed-awaiting-authenticated-merge")
  self.assertIsNone(version["parentVersionId"])
  self.assertFalse(version["approvedTargetChanged"])
  self.assertEqual(version["sourcePacketSha256"],self.packet["contentSha256"])
  self.assertTrue(version["pdfPath"].startswith(SAFE_ROOT+"/"))
 def test_hashed_archive_rejects_modified_or_self_approved_draft(self):
  altered=copy.deepcopy(self.draft)
  altered["fullResearch"]["headline"]="fake changed analyst finding"
  with self.assertRaisesRegex(ValueError,"mutated"):
   validate_unapproved_source(altered,self.packet)
  altered=copy.deepcopy(self.draft)
  altered["approvedTargetPrice"]=999
  with self.assertRaises(ValueError):
   validate_unapproved_source(altered,self.packet)
  altered=copy.deepcopy(self.draft)
  altered["sourcePacketSha256"]="b"*64
  with self.assertRaises(ValueError):
   validate_unapproved_source(altered,self.packet)
 def test_source_version_not_migrated_without_a_protected_review(self):
  approved=copy.deepcopy(EMPTY)
  approved["activeByCompany"][self.packet["companyId"]]="research-v:"+"a"*32
  with self.assertRaisesRegex(ValueError,"pointer"):
   validate_current_approved(approved)
 def test_create_real_hebrew_pdf_in_staging_never_overwrite(self):
  try:
   import reportlab
   import bidi.algorithm
  except ImportError:
   self.fail("Hebrew PDF libraries required in CI; install requirements-pulse-release.txt")
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   out=root/"staged"
   result=build_proposal_files(self.packet,self.draft,EMPTY,out,as_of=NOW,simulation=True)
   pdf=out/result["candidateVersion"]["pdfPath"]
   self.assertTrue(pdf.exists())
   data=pdf.read_bytes()
   self.assertTrue(data.startswith(b"%PDF-"))
   self.assertGreater(len(data),2400)
   self.assertEqual(result["pdfSha256"],sha(data))
   self.assertEqual(result["candidateVersion"]["pdfPages"]>=1,True)
   self.assertTrue(result["simulation"])
   self.assertFalse(result["publishAutomatically"])
   self.assertEqual(result["candidateVersion"]["ownerReview"],"required")
   # Same path may not overwrite a preview or an existing approved PDF.
   with self.assertRaisesRegex(ValueError,"Output staging"):
    build_proposal_files(self.packet,self.draft,EMPTY,out,as_of=NOW,simulation=True)
   self.assertEqual(pdf.read_bytes(),data)
   meta=json.loads((out/"release-proposal.json").read_text(encoding="utf-8"))
   self.assertEqual(meta["pdfSha256"],sha(data))
 def test_unknown_prior_history_cannot_be_silently_replaced(self):
  with self.assertRaisesRegex(ValueError,"historical"):
   validate_current_approved({"version":1,"versions":[{"id":"research-v:"+"1"*32}],"activeByCompany":{}})

if __name__=="__main__":unittest.main()
