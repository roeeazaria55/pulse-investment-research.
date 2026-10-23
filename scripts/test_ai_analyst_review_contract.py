import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ai_research_packets import build_all
from ai_analyst_review_contract import validate_ai_proposal

class AIAnalystProposalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=build_all()["DLO"]

    def proposal(self):
        p=self.packet
        o=p["financialObservations"][0]
        return {
            "version":1,"companyId":p["companyId"],
            "packetContentSha256":p["contentSha256"],
            "status":"requires-human-review",
            "analysisMode":"model-generated-unverified",
            "evidenceCitations":[{"evidenceId":o["observationId"],
                                  "kind":"financial-observation",
                                  "claim":"Issuer table reports a quarterly observation; review required.",
                                  "uncertainty":"Source was revised and needs reconciliation."}],
            "analystQuestions":["Has this exact issuer SHA been reconciled?"],
            "interpretations":[{"observation":"Source reports a financial amount.",
                                "hypothesis":"Changes may warrant fresh gross margin review.",
                                "evidenceIds":[o["observationId"]],
                                "unknowns":["Exact comparability and approval unverified"]}],
            "suggestedScenarioReview":[],
            "proposedValuationAction":"no-automatic-change",
        }

    def test_real_source_bound_review_has_zero_model_mutations(self):
        valid=validate_ai_proposal(self.packet,self.proposal())
        self.assertTrue(valid["valid"])
        self.assertEqual(valid["modelChanges"],0)
        self.assertEqual(valid["status"],"requires-human-review")

    def test_untrusted_model_cannot_self_approve(self):
        base=self.proposal()
        for name,value in [("status","approved"),("proposedValuationAction","update-price-target"),
                           ("companyId","us-smci-nasdaq-common"),
                           ("packetContentSha256","a"*64)]:
            modified={**base,name:value}
            with self.assertRaises(ValueError):
                validate_ai_proposal(self.packet,modified)

    def test_rejects_hallucinated_citation_and_uncited_scenario(self):
        p=self.proposal()
        p["evidenceCitations"][0]["evidenceId"]="observation:hallucinated"
        with self.assertRaisesRegex(ValueError,"Fabricated"):
            validate_ai_proposal(self.packet,p)
        p=self.proposal()
        p["interpretations"][0]["evidenceIds"]=["unknown-evidence"]
        with self.assertRaises(ValueError):validate_ai_proposal(self.packet,p)

    def test_review_scenario_probabilities_need_per_company_evidence_and_full_distribution(self):
        p=self.proposal()
        ids=[c["evidenceId"] for c in p["evidenceCitations"]]
        p["suggestedScenarioReview"]=[
            {"id":name,"suggestedProbability":prob,"reason":"Evidence is incomplete; request review",
             "evidenceIds":ids,"status":"review-only"}
            for name,prob in [("bear",20),("base",50),("bull",30)]]
        self.assertEqual(validate_ai_proposal(self.packet,p)["scenarioSuggestions"],3)
        p["suggestedScenarioReview"][0]["suggestedProbability"]=40
        with self.assertRaisesRegex(ValueError,"100 percent"):
            validate_ai_proposal(self.packet,p)
        p["suggestedScenarioReview"][0]["suggestedProbability"]=20
        p["suggestedScenarioReview"][0]["evidenceIds"]=[]
        with self.assertRaisesRegex(ValueError,"Uncited"):
            validate_ai_proposal(self.packet,p)

    def test_cannot_create_scenario_weights_for_company_without_structured_model(self):
        q=build_all()["SMCI"]
        p=self.proposal()
        p["companyId"]=q["companyId"]
        p["packetContentSha256"]=q["contentSha256"]
        p["evidenceCitations"]=[]
        p["interpretations"]=[]
        p["suggestedScenarioReview"]=[
            {"id":name,"suggestedProbability":prob,"reason":"placeholder",
             "evidenceIds":["missing"],"status":"review-only"}
            for name,prob in [("bear",20),("base",50),("bull",30)]]
        with self.assertRaisesRegex(ValueError,"require current quantified model"):
            validate_ai_proposal(q,p)

    def test_rejects_code_execution_fields_and_missing_limits(self):
        p=self.proposal()
        p["command"]="git push origin main"
        with self.assertRaisesRegex(ValueError,"Unexpected"):
            validate_ai_proposal(self.packet,p)
        p=self.proposal()
        p["evidenceCitations"][0]["uncertainty"]=""
        with self.assertRaises(ValueError):validate_ai_proposal(self.packet,p)

if __name__=="__main__":
    unittest.main()
