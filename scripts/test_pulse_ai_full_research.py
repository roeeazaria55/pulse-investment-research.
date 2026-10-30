"""Full financial research schema: source binding, unknowns and immutable targets."""
import copy
import unittest
from ai_research_packets import build_all
from pulse_ai_full_research import SECTIONS,LIMITATION_TEXT,validate_full_research,build_public_full_research_draft

class FullResearchContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packet=build_all()["DLO"]
 def model(self,mode="model-generated-unverified"):
  p=self.packet
  o=p["financialObservations"][0]["observationId"]
  sections={key:{"summary":"נמצא נתון חשבונאי בדוח הדורש אימות.",
                 "interpretation":"הנתון עשוי להשפיע על תחזית ההכנסות, אך טרם אומת.",
                 "evidenceIds":[o],"unknowns":["עדיין לא ידועה ההשפעה על השווי"]}
            for key in SECTIONS}
  return {"version":2,"companyId":p["companyId"],"packetContentSha256":p["contentSha256"],
   "status":"requires-human-review","analysisMode":mode,
   "headline":"סקירת דוח DLO — טיוטה בלבד",
   "executiveSummary":"הנתונים מחייבים אימות מקורות לפני כל שינוי בתזה.",
   "sections":sections,
   "evidenceCitations":[{"evidenceId":o,"kind":"financial-observation",
                         "claim":"מקור רשמי כולל מדד פיננסי שממתין לביקורת.",
                         "uncertainty":"המועד וההגדרה טעונים התאמה"}],
   "analystQuestions":["האם המדד תואם לתקופת ההשוואה?"],
   "suggestedScenarioReview":[],"targetPriceProposal":None,
   "proposedValuationAction":"no-automatic-change",
   "limitations":["אין תחזית מאושרת להשוואת beat/miss"],"confidence":"low"}
 def test_complete_ten_section_report_cites_packet_and_cannot_approve_target(self):
  v=self.model()
  with self.assertRaisesRegex(ValueError,"provenance"):
   validate_full_research(self.packet,v)
  result=validate_full_research(self.packet,v,model_execution_attested=True)
  self.assertEqual(result["sections"],10)
  self.assertEqual(result["modelChanges"],0)
  draft=build_public_full_research_draft(self.packet,v,"gpt-6.1-sol",execution_attested=True)
  self.assertEqual(draft["fullResearch"]["contractVersion"],2)
  self.assertEqual(draft["publicationStatus"],"not-approved")
  self.assertIsNone(draft["approvedTargetPrice"])
 def test_forged_prices_citations_or_omissions_fail(self):
  v=self.model();v["targetPriceProposal"]=999
  with self.assertRaises(ValueError):
   validate_full_research(self.packet,v,model_execution_attested=True)
  v=self.model();v["sections"].pop("cashFlow")
  with self.assertRaisesRegex(ValueError,"sections"):
   validate_full_research(self.packet,v,model_execution_attested=True)
  v=self.model();v["sections"]["riskChanges"]["evidenceIds"]=["issuer-metric:invented"]
  with self.assertRaises(ValueError):
   validate_full_research(self.packet,v,model_execution_attested=True)
 def test_uncited_section_must_explicitly_admit_data_gap(self):
  v=self.model();v["sections"]["balanceSheet"]["evidenceIds"]=[]
  with self.assertRaisesRegex(ValueError,"Uncited"):
   validate_full_research(self.packet,v,model_execution_attested=True)
  v["sections"]["balanceSheet"]["interpretation"]=LIMITATION_TEXT
  result=validate_full_research(self.packet,v,model_execution_attested=True)
  self.assertEqual(result["interpretations"],9)
 def test_tampered_packet_sha_never_passes(self):
  v=self.model();v["packetContentSha256"]="a"*64
  with self.assertRaises(ValueError):
   validate_full_research(self.packet,v,model_execution_attested=True)
 def test_mock_model_mode_is_distinct_from_real_attestation(self):
  v=self.model(mode="deterministic-no-ai")
  self.assertTrue(validate_full_research(self.packet,v)["valid"])
  with self.assertRaisesRegex(ValueError,"provenance"):
   build_public_full_research_draft(self.packet,v,"gpt-6.1-sol",execution_attested=True)

if __name__=="__main__":unittest.main()
