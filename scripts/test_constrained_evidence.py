"""Constrain provider references while retaining the local financial contract."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ai_research_packets import build_all
from ai_analyst_review_contract import evidence_catalog
from pulse_responses_schema import build_strict_format
from run_optional_ai_review import parse_and_validate,run_paid_review
import test_pulse_ai_full_research as fixtures

class ConstrainedEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packets=build_all()
  cls.fixture=fixtures.FullResearchContractTests();cls.fixture.packet=cls.packets['DLO']
 def response(self,proposal):
  return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(proposal)}]}]}
 def test_schema_binds_all_reference_locations_for_every_company(self):
  for packet in self.packets.values():
   with self.subTest(company=packet['companyId']):
    expected=sorted(evidence_catalog(packet))
    if not expected:
     with self.assertRaisesRegex(ValueError,'No evidence'):build_strict_format(packet)
     continue
    schema=build_strict_format(packet)['schema']
    self.assertNotIn('kind',schema['properties']['evidenceCitations']['items']['properties'])
    found=[]
    def walk(node):
     for key,value in node.get('properties',{}).items():
      if key=='evidenceId':self.assertEqual(value['enum'],expected);found.append(key)
      if key=='evidenceIds':self.assertEqual(value['items']['enum'],expected);found.append(key)
      walk(value)
     if 'items' in node:walk(node['items'])
    walk(schema)
    self.assertGreaterEqual(len(found),12)
 def test_provider_id_gets_kind_and_full_local_validation(self):
  proposal=self.fixture.model();del proposal['evidenceCitations'][0]['kind']
  result=parse_and_validate(self.fixture.packet,self.response(proposal))
  self.assertEqual(result['evidenceCitations'][0]['kind'],'financial-observation')
  self.assertIsNone(result['targetPriceProposal'])
 def test_unknown_id_wrong_kind_and_foreign_company_are_rejected(self):
  for mode in ['unknown','kind','foreign','section']:
   proposal=self.fixture.model()
   citation=proposal['evidenceCitations'][0]
   if mode=='kind':citation['kind']='archived-forecast'
   elif mode=='section':proposal['sections']['cashFlow']['evidenceIds']=['made-up-id']
   else:
    del citation['kind']
    foreign=set(evidence_catalog(self.packets['NBIS']))-set(evidence_catalog(self.fixture.packet))
    citation['evidenceId']=next(iter(foreign)) if mode=='foreign' else 'made-up-id'
   with self.subTest(mode=mode),self.assertRaises(ValueError):
    parse_and_validate(self.fixture.packet,self.response(proposal))
 def test_tampered_packet_fails_before_reservation_or_network(self):
  packet=copy.deepcopy(self.fixture.packet);packet['companyId']='forged'
  with tempfile.TemporaryDirectory() as folder,patch('run_optional_ai_review.urlopen') as network:
   ledger=Path(folder)/'ledger.json'
   with self.assertRaisesRegex(ValueError,'SHA-256'):
    run_paid_review('DLO',packet,'{}','gpt-6.1-sol','fake',Path(folder)/'out.json',ledger)
   network.assert_not_called();self.assertFalse(ledger.exists())
if __name__=='__main__':unittest.main()
