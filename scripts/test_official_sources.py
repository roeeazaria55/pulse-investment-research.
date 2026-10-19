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

class IssuerDistributionTests(unittest.TestCase):
    def test_wrong_publisher_cannot_become_official_company_news(self):
        from official_metadata import OfficialPage
        config={'version':1,'companies':[{'id':'test-issuer','ticker':'IREN','name':'IREN','allowedHosts':['www.globenewswire.com'],'documentPaths':['/news-release/'],'sources':[{'id':'issuer-wire','label':'Issuer releases','url':'https://www.globenewswire.com/search/organization/IREN%2520Limited','kind':'issuer-distributed'}]}]}
        def getter(url,hosts):
            p=OfficialPage()
            if '/search/' in url:
                p.feed('''<main><article><a href="/search/organization/IREN%2520Limited">IREN</a><a href="/news-release/actual">IREN reports financial results</a></article><article><a href="/search/organization/Law%2520Firm">Law firm</a><a href="/news-release/wrong">IREN investor investigation announced by a law firm</a></article></main>''')
            else:p.feed('<h1>IREN reports financial results</h1><meta property="article:published_time" content="2026-10-14T10:00:00Z">')
            return p
        result=collect(config,{},NOW,getter)
        self.assertEqual(len(result['items']),1)
        self.assertTrue(result['items'][0]['url'].endswith('/actual'))
        self.assertEqual(result['items'][0]['sourceKind'],'issuer-distributed')
        self.assertEqual(result['items'][0]['publishedDate'],'2026-10-14')
        self.assertEqual(result['items'][0]['dateEvidenceUrl'],result['items'][0]['url'])
    def test_distributor_without_publisher_proof_is_failed(self):
        from official_metadata import OfficialPage
        config={'version':1,'companies':[{'id':'test-issuer','ticker':'IREN','name':'IREN','allowedHosts':['www.globenewswire.com'],'documentPaths':['/news-release/'],'sources':[{'id':'issuer-wire','label':'Issuer releases','url':'https://www.globenewswire.com/search/organization/IREN%2520Limited','kind':'issuer-distributed'}]}]}
        def getter(*_):
            p=OfficialPage();p.feed('<a href="/news-release/wrong">IREN mentioned in a third-party release</a>');return p
        result=collect(config,{},NOW,getter)
        self.assertEqual(result['items'],[]);self.assertEqual(result['sources'][0]['status'],'failed')

class NavigationTests(unittest.TestCase):
    def test_navigation_cannot_starve_reports_or_survive_successful_refresh(self):
        from official_metadata import OfficialPage
        c={'id':'gilat','ticker':'','name':'Gilat Telecom','allowedHosts':['example.org'],'documentPaths':['/uploads/'],'sources':[{'id':'financials','url':'https://example.org/financials','label':'Reports'}]}
        config={'companies':[c]}
        nav=''.join(f'<a href="/uploads/policy{i}.pdf">Policy {i}</a>' for i in range(12))
        def page(html):
            p=OfficialPage();p.feed(html);return p
        polluted=collect(config,{},NOW,lambda *_:page(nav))
        self.assertEqual(len(polluted['items']),8)
        html=f'<header><nav>{nav}</nav></header><main><article><h3>Q2 2026 financial report</h3><a href="/uploads/q2.pdf">Download</a></article></main><footer>{nav}</footer>'
        fixed=collect(config,polluted,NOW,lambda *_:page(html))
        self.assertEqual([x['url'] for x in fixed['items']],['https://example.org/uploads/q2.pdf'])
        self.assertEqual(fixed['sources'][0]['count'],1)
        self.assertIsNone(fixed['items'][0]['publishedDate'])
        def blocked(*_):raise ValueError('HTTP 403')
        self.assertEqual(collect(config,polluted,NOW,blocked)['items'],polluted['items'])
    def test_body_copy_overrides_menu_and_does_not_remove_other_company(self):
        from official_metadata import OfficialPage
        for html in ('<nav><a href="/a.pdf">Menu</a></nav><main><a href="/a.pdf">Report</a></main>', '<main><a href="/a.pdf">Report</a></main><footer><a href="/a.pdf">Menu</a></footer>'):
            p=OfficialPage();p.feed(html)
            self.assertFalse(p.link_contexts['/a.pdf']['navigationOnly'])
        for wrapper in ('<div role="navigation">','<div class="elementor-nav-menu">'):
            p=OfficialPage();p.feed(wrapper+'<a href="/a.pdf">Menu PDF</a></div>')
            self.assertTrue(p.link_contexts['/a.pdf']['navigationOnly'])
    def test_navigation_cleanup_is_scoped_to_the_source_that_collected_it(self):
        from official_metadata import OfficialPage
        c={'id':'issuer','ticker':'','name':'Issuer','allowedHosts':['example.org'],'documentPaths':['/uploads/'],'sources':[{'id':'body','url':'https://example.org/body','label':'Reports'},{'id':'menu','url':'https://example.org/menu','label':'Other'}]}
        def getter(url,*_):
            p=OfficialPage();tag='main' if url.endswith('/body') else 'nav'
            p.feed(f'<{tag}><a href="/uploads/report.pdf">Annual report 2025</a></{tag}>');return p
        result=collect({'companies':[c]}, {},NOW,getter)
        self.assertEqual(len(result['items']),1);self.assertEqual(result['items'][0]['sourceId'],'body')
        self.assertEqual(result['sources'][1]['status'],'failed')
