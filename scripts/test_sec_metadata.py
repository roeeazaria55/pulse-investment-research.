import unittest
from sec_metadata import submissions_page

class SecTests(unittest.TestCase):
    def setUp(self):
        self.source={'cik':'1326801','url':'https://data.sec.gov/submissions/CIK0001326801.json'}
        self.company={'ticker':'META','name':'Meta','documentPaths':['/Archives/edgar/data/1326801/']}
        self.payload={'cik':'0001326801','tickers':['META'],'filings':{'recent':{'form':['10-Q','4','8-K'],'filingDate':['2026-08-01']*3,'accessionNumber':['0001326801-26-000001']*3,'primaryDocument':['meta.htm','ownership.xml','../other.htm']}}}
    def test_only_supported_safe_issuer_documents(self):
        p=submissions_page(self.source,self.company,lambda _:self.payload)
        self.assertEqual(len(p.links),1)
        self.assertIn('/1326801/000132680126000001/meta.htm',p.links[0][0])
        self.assertIn('filed 2026-08-01',p.links[0][1])
        self.assertNotIn('publishedDate',p.link_contexts[p.links[0][0]])
    def test_identity_mismatch_rejected(self):
        self.payload['tickers']=['OTHER']
        with self.assertRaises(ValueError):submissions_page(self.source,self.company,lambda _:self.payload)
    def test_source_url_and_archive_must_match(self):
        self.source['url']='https://example.com/data.json'
        with self.assertRaises(ValueError):submissions_page(self.source,self.company,lambda _:self.payload)
    def test_generic_report_and_section_titles_preserve_file_identity(self):
        from official_metadata import describe
        c={'name':'Lemonade'}
        result=describe(c,'https://www.lemonade.com/LMND-Q2-2026.pdf','Shareholder letter')
        self.assertIn('Q2 2026',result['title'])
        result=describe(c,'https://www.lemonade.com/release','Lemonade financial results',page_title='Release Details')
        self.assertEqual(result['title'],'Lemonade financial results')
