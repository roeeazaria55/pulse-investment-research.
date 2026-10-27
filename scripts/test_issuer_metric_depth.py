"""Regression against actually retained originals, plus hostile layout mutations."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from issuer_coverage import build
from issuer_table_adapters import adapted_issuer_facts
from financial_readout import source_margins
from ftai_sec_companyfacts import read_ftai_companyfacts,SEC_URL

ROOT=Path(__file__).resolve().parent.parent
class DepthTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.registry=json.loads((ROOT/'public/data/official-registry.json').read_text())
  cls.intake=json.loads((ROOT/'public/data/report-intake.json').read_text())
  cls.coverage={r['companyId']:r for r in build(cls.registry,cls.intake)['coverage']}
 def doc(self,cid):
  ident=self.coverage[cid]['report']['id']
  return copy.deepcopy(next(d for d in self.intake['documents'] if d['id']==ident))
 def test_ftai_original_bytes_digest_and_half_year_cash_are_retained(self):
  c=next(c for c in self.registry['companies'] if c['id']=='candidate-ftai')
  raw=(ROOT/'public/data/source-evidence/ftai-companyfacts-20261026.json').read_bytes()
  d=read_ftai_companyfacts(raw,SEC_URL,c)
  self.assertEqual(d['sha256'],hashlib.sha256(raw).hexdigest())
  self.assertEqual(d['sha256'],self.coverage[c['id']]['report']['sha256'])
  m={m['id']:m for m in self.coverage[c['id']]['typedMetrics']}
  self.assertEqual(m['revenue']['periodStart'],'2026-04-01')
  self.assertEqual(m['operatingCash']['periodStart'],'2026-01-01')
  self.assertEqual(m['operatingCash']['value'],-265.303)
  self.assertEqual(m['commonNetIncome']['value'],117.585)
 def test_nebius_negative_cash_comparative_and_balance_date(self):
  m={m['id']:m for m in self.coverage['candidate-nebius']['typedMetrics']}
  self.assertEqual(m['operatingCash']['previousValue'],-171.6)
  self.assertEqual(m['capex']['value'],5657.4)
  self.assertEqual(m['capex']['sourceRaw'],'(5,657.4)')
  self.assertEqual(m['cash']['previousPeriodEnd'],'2025-12-31')
  self.assertEqual(m['cash']['periodStart'],m['cash']['periodEnd'])
 def test_nebius_extra_rows_fail_closed_on_year_change_or_ambiguity(self):
  d=self.doc('candidate-nebius')
  p=next(p for p in d['sourcePdfPages'] if p['page']==7)
  p['text']=p['text'].replace('2025 2026 2025 2026','2024 2026 2024 2026')
  self.assertNotIn('operatingIncome',{m['id'] for m in adapted_issuer_facts(d)})
  d=self.doc('candidate-nebius');p=next(p for p in d['sourcePdfPages'] if p['page']==7)
  p['text']+='\nLoss from operations (111.2) (175.9) (231.5) (303.9)'
  self.assertNotIn('operatingIncome',{m['id'] for m in adapted_issuer_facts(d)})
 def test_iren_original_annual_not_adjacent_quarter_columns(self):
  m={m['id']:m for m in self.coverage['candidate-iren']['typedMetrics']}
  self.assertEqual(m['aiRevenue']['value'],128.8)
  self.assertEqual(m['aiRevenue']['previousValue'],16.4)
  self.assertEqual(m['capex']['value'],4333.1)
 def test_lemonade_non_gaap_and_instant_are_explicit(self):
  m={m['id']:m for m in self.coverage['us-lmnd-nyse-common']['typedMetrics']}
  self.assertIn('Non-GAAP',m['adjustedEbitda']['accountingBasis'])
  self.assertEqual(m['inForcePremium']['periodStart'],m['inForcePremium']['periodEnd'])
  self.assertEqual(m['netIncome']['value'],-43.4)
 def test_meta_cash_ppe_is_not_total_capex(self):
  m={m['id']:m for m in self.coverage['us-meta-nasdaq-a']['typedMetrics']}
  self.assertEqual(m['capex']['value'],33942)
  self.assertEqual(m['capex']['sourceRaw'],'(33,942)')
  self.assertIn('excludes finance-lease',m['capex']['accountingBasis'])
 def test_margin_rejects_mixed_gaap_duplicate_ids_and_missing_provenance(self):
  original=self.coverage['candidate-sandisk']['typedMetrics']
  for mutation in ('non-gaap','duplicate','missing'):
   m=copy.deepcopy(original)
   if mutation=='non-gaap':next(x for x in m if x['id']=='grossProfit')['accountingBasis']='Non-GAAP adjusted gross profit'
   if mutation=='duplicate':m.append(copy.deepcopy(m[0]))
   if mutation=='missing':
    for x in m:x['sourceSha256']=None
   margins=source_margins(m)
   if mutation=='non-gaap':self.assertNotIn('grossProfit',{x['metricId'] for x in margins})
   else:self.assertEqual(margins,[])
