import copy,json,unittest
from pathlib import Path
from earnings import Page
from official_sources import collect,date_only,kind
NOW='2026-10-18T16:00:00+00:00'
CONFIG=json.loads(Path('public/data/official-registry.json').read_text())
class OfficialTests(unittest.TestCase):
    def setUp(self):
        self.config=copy.deepcopy(CONFIG);self.config['companies']=self.config['companies'][:1]
        self.company=self.config['companies'][0];self.company['sources']=self.company['sources'][:1]
    def getter(self,url,hosts):
        p=Page()
        if url==self.company['sources'][0]['url']:
            p.links=[('/newsroom/nebius-results','Nebius reports financial results'),('/newsroom/nebius-results','Nebius reports financial results duplicate'),('https://evil.test/newsroom/inject','Malicious link test'),('/pricing','Pricing navigation')]
        else:p.feed('<h1>Nebius reports financial results</h1><meta property="article:published_time" content="2026-10-16T12:00:00Z">')
        return p
    def test_allowlisted_links_stable_identity_and_metadata_scope(self):
        a=collect(self.config,{},NOW,self.getter)
        self.assertEqual(len(a['items']),1);self.assertEqual(a['sources'][0]['count'],1)
        n=a['items'][0];self.assertEqual(n['publishedDate'],'2026-10-16');self.assertEqual(n['kind'],'results')
        self.assertEqual(n['metadataStatus'],'page-metadata');self.assertEqual(n['contentScope'],'metadata-only')
        b=collect(self.config,a,'2026-10-19T16:00:00+00:00',self.getter)
        self.assertEqual(n['id'],b['items'][0]['id']);self.assertEqual(n['collectedAt'],b['items'][0]['collectedAt'])
        self.assertNotEqual(n['lastSeenAt'],b['items'][0]['lastSeenAt'])
    def test_failure_preserves_items_and_success_timestamp(self):
        a=collect(self.config,{},NOW,self.getter)
        def blocked(*_):raise ValueError('HTTP 403')
        b=collect(self.config,a,'2026-10-19T16:00:00+00:00',blocked)
        self.assertEqual(a['items'],b['items']);self.assertEqual(b['sources'][0]['status'],'failed')
        self.assertEqual(b['sources'][0]['lastSuccessfulAt'],NOW)
    def test_empty_dynamic_page_is_failure_not_no_news(self):
        a=collect(self.config,{},NOW,lambda *_:Page())
        self.assertEqual(a['sources'][0]['status'],'failed');self.assertEqual(a['items'],[])
    def test_detail_failure_still_exposes_index_link_without_claiming_read(self):
        def getter(url,hosts):
            if url==self.company['sources'][0]['url']:return self.getter(url,hosts)
            raise ValueError('HTTP 403')
        a=collect(self.config,{},NOW,getter);n=a['items'][0]
        self.assertEqual(n['metadataStatus'],'index-link');self.assertIsNone(n['publishedDate'])
        self.assertIsNone(n['metadataCheckedAt']);self.assertEqual(n['metadataError'],'HTTP 403')
    def test_date_and_event_kind_do_not_invent_release_time(self):
        self.assertIsNone(date_only('August 27, 2026'));self.assertIsNone(date_only('2026-02-30'))
        self.assertEqual(kind('IREN to Release FY26 Results','https://example.org/a'),'schedule')
        self.assertEqual(kind('IREN Reports FY26 Results','https://example.org/a'),'results')
        self.assertEqual(kind('Download','https://example.org/static-files/a'),'document')
    def test_bounded_detail_requests_and_no_pdf_fetch(self):
        calls=[]
        def getter(url,hosts):
            calls.append(url);p=Page()
            if url==self.company['sources'][0]['url']:
                p.links=[('/newsroom/release-'+str(i),'Nebius release '+str(i)) for i in range(30)]
                p.links.insert(0,('https://assets.nebius.com/assets/file.pdf','Nebius report PDF'))
            else:p.feed('<h1>Nebius release title</h1>')
            return p
        a=collect(self.config,{},NOW,getter)
        self.assertEqual(len(a['items']),8);self.assertEqual(len(calls),4)
        self.assertFalse(any(u.endswith('.pdf') for u in calls))
