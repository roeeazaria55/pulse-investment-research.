"""Public UI drafts are unapproved and append-only. No model is called."""
import copy
import unittest
from ai_research_packets import build_all
from pulse_ai_research_drafts import build_public_draft, append_public

class AIResearchDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=build_all()["DLO"]
    def draft(self):
        p=self.packet
        observation=p["financialObservations"][0]["observationId"]
        return {"version":1,"companyId":p["companyId"],"packetContentSha256":p["contentSha256"],
                "status":"requires-human-review","analysisMode":"model-generated-unverified",
                "evidenceCitations":[{"evidenceId":observation,"kind":"financial-observation",
                                      "claim":"מקור מדווח על נתון להכנסות","uncertainty":"טעון בדיקה"}],
                "analystQuestions":["בדוק מקור"],"interpretations":[],
                "suggestedScenarioReview":[],"proposedValuationAction":"no-automatic-change"}
    def test_unapproved_ai_draft_and_immutable_versions(self):
        proposal=self.draft()
        with self.assertRaisesRegex(ValueError,"attestation"):
            build_public_draft(self.packet,proposal,"gpt-6.1-sol")
        draft=build_public_draft(self.packet,proposal,"gpt-6.1-sol",execution_attested=True)
        self.assertEqual(draft["analysisMode"],"model-generated-unverified")
        self.assertIsNone(draft["approvedTargetPrice"])
        self.assertEqual(draft["publicationStatus"],"not-approved")
        first=append_public({},draft,"2026-10-29T00:00:00+00:00")
        rerun=append_public(first,draft,"2026-10-30T00:00:00+00:00")
        self.assertEqual(rerun["newDraftCount"],0)
        self.assertEqual(len(rerun["drafts"]),1)
        revised=copy.deepcopy(proposal)
        revised["analystQuestions"]=["Review earnings quality before any target update"]
        changed=build_public_draft(self.packet,revised,"gpt-6.1-sol",execution_attested=True)
        third=append_public(rerun,changed,"2026-10-30T00:00:00+00:00")
        self.assertEqual(third["newDraftCount"],1)
        self.assertEqual(len(third["drafts"]),2)
    def test_never_trust_edited_history_or_self_approval(self):
        d=build_public_draft(self.packet,self.draft(),"gpt-6-luna",execution_attested=True)
        first=append_public({},d,"2026-10-29T00:00:00Z")
        first["drafts"][0]["analystQuestions"]=["forged"]
        with self.assertRaisesRegex(ValueError,"modified"):
            append_public(first,d,"2026-10-29T00:00:00Z")
        bad=self.draft();bad["proposedValuationAction"]="update-price-target"
        with self.assertRaises(ValueError):
            build_public_draft(self.packet,bad,"gpt-6.1-sol",execution_attested=True)

if __name__=="__main__":unittest.main()
