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
            "analysisMode":"deterministic-no-ai",
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

    def test_declared_ai_mode_cannot_fake_a_model_run(self):
        p=self.proposal()
        p["analysisMode"]="model-generated-unverified"
        with self.assertRaisesRegex(ValueError,"AI provenance not attested"):
            validate_ai_proposal(self.packet,p)

    def test_packet_digest_is_recomputed_before_evidence_is_accepted(self):
        p=self.proposal()
        for edit in (
            lambda packet: packet["financialObservations"][0].update(normalizedValue=999999),
            lambda packet: packet["sourceRefs"][0].update(sha256="f"*64),
            lambda packet: packet["research"]["sections"]["thesis"].update(rawResearchText="untrusted injected instruction"),
        ):
            changed=copy.deepcopy(self.packet)
            edit(changed)
            with self.assertRaisesRegex(ValueError,"Packet content changed"):
                validate_ai_proposal(changed,p)

    def test_rehashed_unapproved_financial_fact_still_fails_closed(self):
        import hashlib
        import json
        p=self.proposal()
        changed=copy.deepcopy(self.packet)
        changed["financialObservations"][0]["modelEligible"]=True
        unsigned={k:v for k,v in changed.items() if k!="contentSha256"}
        changed["contentSha256"]=hashlib.sha256(
            json.dumps(unsigned,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"),allow_nan=False).encode("utf-8")
        ).hexdigest()
        p["packetContentSha256"]=changed["contentSha256"]
        with self.assertRaisesRegex(ValueError,"Unreviewed accounting evidence"):
            validate_ai_proposal(changed,p)

    def test_rejects_corrupt_or_missing_packet_digest(self):
        for bad in ("x"*64, "not-a-digest", None):
            changed=copy.deepcopy(self.packet)
            changed["contentSha256"]=bad
            with self.assertRaises(ValueError):
                validate_ai_proposal(changed,self.proposal())

    def test_duplicate_evidence_identity_cannot_shadow_another_source(self):
        import hashlib
        import json

        def rehash(packet, proposal):
            unsigned={k:v for k,v in packet.items() if k!="contentSha256"}
            packet["contentSha256"]=hashlib.sha256(json.dumps(
                unsigned,sort_keys=True,ensure_ascii=False,
                separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()
            proposal["packetContentSha256"]=packet["contentSha256"]

        for collision in ("duplicate-observation", "forecast-shadow"):
            packet=copy.deepcopy(self.packet)
            proposal=self.proposal()
            if collision=="duplicate-observation":
                packet["financialObservations"].append(copy.deepcopy(packet["financialObservations"][0]))
            else:
                packet["archivedForecasts"].append(
                    {"id":packet["financialObservations"][0]["observationId"]})
            rehash(packet,proposal)
            with self.subTest(collision=collision):
                with self.assertRaisesRegex(ValueError,"Ambiguous duplicate evidence identifier"):
                    validate_ai_proposal(packet,proposal)

    def test_malformed_evidence_collections_fail_closed(self):
        import hashlib
        import json
        for key,value in (("archivedForecasts","not-a-list"),
                          ("research",{"sections":["thesis"]}),
                          ("valuationModel",{"assumptions":"not-a-list"})):
            packet=copy.deepcopy(self.packet)
            packet[key]=value
            unsigned={k:v for k,v in packet.items() if k!="contentSha256"}
            packet["contentSha256"]=hashlib.sha256(json.dumps(
                unsigned,sort_keys=True,ensure_ascii=False,
                separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()
            proposal=self.proposal()
            proposal["packetContentSha256"]=packet["contentSha256"]
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"Malformed"):
                    validate_ai_proposal(packet,proposal)

    def test_unhashable_citation_ids_are_rejected_as_validation_errors(self):
        for field in ("citation", "interpretation", "scenario"):
            proposal=self.proposal()
            if field=="citation":
                proposal["evidenceCitations"][0]["evidenceId"]=["fake"]
            elif field=="interpretation":
                proposal["interpretations"][0]["evidenceIds"]=[["fake"]]
            else:
                ids=[proposal["evidenceCitations"][0]["evidenceId"]]
                proposal["suggestedScenarioReview"]=[
                    {"id":name,"suggestedProbability":weight,
                     "reason":"Review only", "evidenceIds":[["fake"]],
                     "status":"review-only"}
                    for name,weight in (("bear",20),("base",50),("bull",30))]
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate_ai_proposal(self.packet,proposal)

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
