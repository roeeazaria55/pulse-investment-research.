import copy
import hashlib
import json
import unittest
from report_context import extract_context,validate_context
from report_intake import extract,KNOWN_FACTS
from issuer_coverage import XBRL,safe_source_facts
from test_report_intake import HTML,C,URL
from ai_research_packets import build_all
from ai_analyst_review_contract import evidence_catalog
from pulse_responses_schema import build_strict_format

class ReportDepthTests(unittest.TestCase):
 def test_all_supported_xbrl_concepts_survive_intake(self):
  self.assertFalse(set(XBRL)-KNOWN_FACTS)
  capex=HTML.replace(b'us-gaap:Revenues',b'us-gaap:PaymentsToAcquirePropertyPlantAndEquipment')
  facts=extract(capex,'text/html',URL,C)['facts']
  self.assertEqual(facts[0]['concept'],'us-gaap:paymentstoacquirepropertyplantandequipment')
 def test_repeated_contexts_cannot_crowd_out_capex(self):
  from report_intake import ReportHTML,inline_facts
  page=ReportHTML();page.units={'usd':'iso4217:USD'}
  page.contexts={str(i):{'identifier':'1375365','startdate':'2025-07-01','enddate':'2026-06-30'} for i in range(161)}
  page.facts=[{'name':'us-gaap:revenues','context':str(i),'unit':'usd','scale':'0','sign':'','text':['1'],'format':''} for i in range(160)]
  page.facts.append({**page.facts[0],'name':'us-gaap:paymentstoacquirepropertyplantandequipment','context':'160'})
  rows=inline_facts(page,C)
  self.assertEqual(len(rows),150)
  self.assertIn('us-gaap:paymentstoacquirepropertyplantandequipment',{r['concept'] for r in rows})
 def test_more_than_eight_supported_metrics_are_not_silently_lost(self):
  facts=[{'concept':c,'unit':'iso4217:USD','start':'2025-07-01','end':'2026-06-30',
          'value':1000000,'context':c} for c in XBRL if c!='us-gaap:revenues']
  doc={'companyId':C['id'],'format':'html','facts':facts,'url':URL,'sha256':'a'*64,'id':'report:test'}
  proposals=safe_source_facts(doc)
  self.assertGreater(len(proposals),8)
  self.assertIn('capex',{r['id'] for r in proposals})
  self.assertTrue(all(r['reviewStatus']=='pending-review' for r in proposals))
 def test_excerpts_bounded_verbatim_and_not_complete_disclosures(self):
  text='x '*1000+' Material weakness in internal controls. We assess liquidity and credit facilities. Business outlook is uncertain.'
  rows=extract_context(text)
  self.assertIn('controls',{r['topic'] for r in rows})
  normalized=' '.join(text.split())
  for r in validate_context(rows):
   self.assertIn(r['text'],normalized);self.assertLessEqual(len(r['text']),800)
   self.assertEqual(r['scope'],'keyword-window-not-complete-disclosure')
  forged=copy.deepcopy(rows);forged[0]['text']+='changed'
  with self.assertRaises(ValueError):validate_context(forged)
  with self.assertRaises(ValueError):validate_context(rows+rows)
 def test_script_content_not_retained_and_reference_constraints_include_excerpts(self):
  html=HTML.replace(b'</html>',b'<script>material weakness SECRET</script><p>Liquidity and working capital require management review.</p></html>')
  rows=extract(html,'text/html',URL,C)['sourceExcerpts']
  self.assertNotIn('SECRET',json.dumps(rows))
  packet=copy.deepcopy(build_all()['SMCI'])
  packet['latestIssuerResearch']['sourceExcerpts']=rows
  packet['latestIssuerResearch']['report']={'digest':extract(html,'text/html',URL,C)['sha256'],'sourceUrl':URL}
  unsigned={k:v for k,v in packet.items() if k!='contentSha256'}
  packet['contentSha256']=hashlib.sha256(json.dumps(unsigned,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
  catalog=evidence_catalog(packet)
  ident='report-excerpt:'+packet['companyId']+':liquidity'
  self.assertEqual(catalog[ident],'report-excerpt')
  schema=build_strict_format(packet)['schema']
  self.assertIn(ident,schema['properties']['evidenceCitations']['items']['properties']['evidenceId']['enum'])
if __name__=='__main__':unittest.main()
