import copy
import unittest
from report_intake import collect,extract,safe_report_url
C={'id':'us-smci-nasdaq-common','name':'Super Micro Computer','label':'SMCI','aliases':['Supermicro'],'allowedHosts':['www.sec.gov'],'documentPaths':['/Archives/edgar/data/1375365/'],'sources':[{'cik':'1375365'}]}
URL='https://www.sec.gov/Archives/edgar/data/1375365/test.htm'
HTML='''<html><h1>Super Micro Computer financial results</h1><script>revenue is fake</script><p>These are financial statements for the company and not an announcement of a future earnings call.</p><table><tr><th>USD millions</th><th>2026</th><th>2025</th></tr><tr><td>Revenue</td><td>100</td><td>80</td></tr></table><xbrli:context id="annual"><xbrli:entity><xbrli:identifier>0001375365</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startdate>2025-07-01</xbrli:startdate><xbrli:enddate>2026-06-30</xbrli:enddate></xbrli:period></xbrli:context><xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit><ix:nonFraction name="us-gaap:Revenues" contextRef="annual" unitRef="usd" scale="6" format="ixt:num-dot-decimal">39,100</ix:nonFraction></html>'''.encode()
ITEM={'id':'official:test','companyId':C['id'],'kind':'document','title':'SMCI annual report','url':URL,'publishedDate':None,'lastSeenAt':'2026-10-20','documentPeriod':'FY2026','periodBasis':'title'}
class IntakeTests(unittest.TestCase):
 def test_scope_and_path_guard(self):
  self.assertTrue(safe_report_url(URL,C))
  for url in ['http://www.sec.gov/Archives/edgar/data/1375365/test.htm','https://www.sec.gov/Archives/edgar/data/other/test.htm','https://evil.test/test.htm','https://www.sec.gov/Archives/edgar/data/1375365/%2e%2e/other.htm','https://user:pass@www.sec.gov/Archives/edgar/data/1375365/test.htm']:
   self.assertFalse(safe_report_url(url,C))
 def test_reads_tables_and_structured_periods_without_guessing(self):
  r=extract(HTML,'text/html',URL,C)
  self.assertEqual(r['status'],'extracted');self.assertEqual(r['tables'][0]['rows'][1],['Revenue','100','80'])
  self.assertEqual(r['facts'][0]['value'],39100000000);self.assertEqual(r['facts'][0]['start'],'2025-07-01');self.assertEqual(r['facts'][0]['end'],'2026-06-30')
  self.assertEqual(r['reviewStatus'],'pending-review');self.assertNotIn('fake',str(r['tables']))
 def test_mismatched_issuer_dimensions_and_locale_do_not_become_group_facts(self):
  for old,new in [('0001375365','0000000001'),('<xbrli:entity>','<xbrli:entity><xbrli:segment>segment</xbrli:segment>'),('ixt:num-dot-decimal','ixt:num-comma-decimal')]:
   r=extract(HTML.replace(old.encode(),new.encode()),'text/html',URL,C)
   self.assertEqual(r['facts'],[])
 def test_schedules_and_user_research_are_not_results(self):
  for title in ['SMCI to report financial results','PULSE / EQUITY RESEARCH / SMCI']:
   html=b'<h1>'+title.encode()+b'</h1><p>'+b'a'*200+b'</p>'
   with self.assertRaises(ValueError):extract(html,'text/html',URL,C)
 def test_revision_and_failed_fetch_preserve_previous_success(self):
  def fetch(url,c):return HTML,'text/html',url
  first=collect({'items':[ITEM]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fetch)
  same=collect({'items':[ITEM]},{'companies':[C]},first,'2026-10-20T13:00:00Z',fetcher=fetch)
  self.assertEqual(len(same['documents']),1);self.assertEqual(same['documents'][0]['firstDetectedAt'],first['documents'][0]['firstDetectedAt']);self.assertFalse(same['documents'][0]['revised']);self.assertIsNone(same['documents'][0]['publishedDate'])
  changed=collect({'items':[ITEM]},{'companies':[C]},same,'2026-10-20T14:00:00Z',fetcher=lambda u,c:(HTML.replace(b'39,100',b'39,200'),'text/html',u))
  self.assertTrue(changed['documents'][0]['revised']);self.assertEqual(len(changed['documents'][0]['revisions']),1)
  def fail(u,c):raise ValueError('offline')
  failed=collect({'items':[ITEM]},{'companies':[C]},changed,'2026-10-20T15:00:00Z',fetcher=fail)
  self.assertEqual(failed['documents'][0]['sha256'],changed['documents'][0]['sha256']);self.assertEqual(failed['documents'][0]['lastSuccessfulAt'],changed['documents'][0]['lastSuccessfulAt']);self.assertEqual(failed['sources'][0]['status'],'failed')
 def test_http_200_with_no_financial_rows_cannot_erase_prior_extracted_evidence(self):
  def fetch_good(url,c):return HTML,'text/html',url
  first=collect({'items':[ITEM]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fetch_good)
  old=first['documents'][0]
  self.assertEqual(old['status'],'extracted')
  # Valid issuer identity and financial title, but zero supported financial data:
  # this can happen after an IR page redesign, blocked dynamic content or a parser regression.
  no_data=(b'<html><h1>Super Micro Computer FY2026 financial results</h1><p>'+
           b'Corporate information and annual reporting context. '*12+b'</p></html>')
  parsed=extract(no_data,'text/html',URL,C)
  self.assertEqual(parsed['status'],'read-no-supported-data')
  second=collect({'items':[ITEM]},{'companies':[C]},first,'2026-10-20T13:00:00Z',
                 fetcher=lambda url,c:(no_data,'text/html',url))
  retained=second['documents'][0]
  self.assertEqual(retained['sha256'],old['sha256'])
  self.assertEqual(retained['facts'],old['facts'])
  self.assertEqual(retained['tables'],old['tables'])
  self.assertEqual(retained['lastSuccessfulAt'],old['lastSuccessfulAt'])
  self.assertEqual(retained['status'],'extracted')
  self.assertIn('retained for reconciliation',retained['error'])
  self.assertEqual(second['sources'][0]['status'],'failed')
  self.assertFalse(retained['revised'])
  # A first-ever unsupported report is still recorded as an honest no-data result.
  fresh=collect({'items':[ITEM]},{'companies':[C]}, {},'2026-10-20T13:00:00Z',
                fetcher=lambda url,c:(no_data,'text/html',url))
  self.assertEqual(fresh['documents'][0]['status'],'read-no-supported-data')

 def test_attached_financial_document_is_followed_with_same_issuer_scope(self):
  parent=b'<h1>SMCI financial results</h1><p>'+b'report '*30+b'</p><a href="attached.htm.pdf">Download financial results</a>'
  calls=[]
  def fetch(url,c):
   calls.append(url)
   return (parent,'text/html',url) if url==URL else (HTML,'text/html',url)
  result=collect({'items':[ITEM]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fetch)
  self.assertEqual(len(calls),2);self.assertTrue(result['documents'][0]['finalUrl'].endswith('attached.htm.pdf'));self.assertEqual(result['documents'][0]['facts'][0]['value'],39100000000)
 def test_clinical_results_are_not_financial_candidates(self):
  item={**ITEM,'title':'SMCI Reports Promising Pilot Study Results','kind':'results'}
  def fail(u,c):self.fail('Clinical release should not be fetched')
  result=collect({'items':[item]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fail)
  self.assertEqual(result['documents'],[])
 def test_zero_budget_and_schedule_skip_fetch(self):
  def fail(u,c):self.fail('Network should not be called')
  result=collect({'items':[ITEM]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fail,limit=0)
  self.assertEqual(result['sources'][0]['status'],'deferred')
  scheduled={**ITEM,'title':'SMCI to report financial results','kind':'schedule'}
  result=collect({'items':[scheduled]},{'companies':[C]}, {},'2026-10-20T12:00:00Z',fetcher=fail)
  self.assertEqual(result['documents'],[])
if __name__=='__main__':unittest.main()
