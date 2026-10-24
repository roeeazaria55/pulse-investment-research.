import copy
import json
import unittest
from pathlib import Path
from collect_articles import collect, relevant, endpoint
from news_poc import parse_google, parse_gdelt, allowed

NOW = '2026-10-18T12:00:00+00:00'
def rss(title='Nebius AI cloud expansion - Test Publisher', date='Sun, 18 Oct 2026 10:00:00 GMT'):
    return ('<rss><channel><item><title>'+title+'</title><link>https://news.google.com/rss/articles/test</link>'
            '<source>Test Publisher</source>'+ ('<pubDate>'+date+'</pubDate>' if date else '')+'</item></channel></rss>').encode()

class ArticleTests(unittest.TestCase):
    def setUp(self):
        self.registry=json.loads(Path('public/data/news-registry.json').read_text(encoding='utf-8'))
        self.registry['companies']=self.registry['companies'][:1]
    def run_collect(self, previous=None, getter=lambda _:rss()):
        return collect(self.registry, previous or {}, NOW, getter, lambda _:None)
    def test_stable_dedup_and_first_collection(self):
        first=self.run_collect()
        second=self.run_collect(first)
        self.assertEqual(len(second['articles']),1)
        self.assertEqual(second['discovery']['newCount'],0)
        self.assertTrue(second['discovery']['noNewItems'])
        self.assertEqual(first['articles'][0]['collectedAt'],second['articles'][0]['collectedAt'])
    def test_missing_and_invalid_publication_never_invented(self):
        for date in ('','invalid'):
            self.assertIsNone(parse_google(rss(date=date))[0]['publishedAt'])
    def test_gdelt_discovery_not_publication(self):
        a=parse_gdelt(json.dumps({'articles':[{'title':'Nebius AI cloud','url':'https://example.org/a','domain':'example.org','seendate':'20261018T100000Z'}]}).encode())[0]
        self.assertIsNone(a['publishedAt'])
        self.assertEqual(a['discoveredAt'],'20261018T100000Z')
    def test_wrong_company_and_context(self):
        registry=json.loads(Path('public/data/news-registry.json').read_text(encoding='utf-8'))
        by_name={c['name']:c for c in registry['companies']}
        self.assertFalse(relevant('Gilat Satellite Networks wins telecom contract',by_name['Gilat Telecom']))
        self.assertTrue(relevant('Gilat Telecom wins connectivity contract',by_name['Gilat Telecom']))
        self.assertFalse(relevant('IREN Energia announces gas tariff',by_name['IREN']))
        self.assertFalse(relevant('Lemonade recipe with fresh lemons',by_name['Lemonade']))
        self.assertFalse(relevant('Meta Materials earnings',by_name['Meta Platforms']))
        self.assertTrue(relevant('IREN AI cloud expansion',by_name['IREN']))
    def test_blocked_preserves_previous(self):
        prior=self.run_collect()
        def blocked(_): raise ValueError('HTTP 403 blocked')
        result=self.run_collect(prior,blocked)
        self.assertEqual(result['articles'],prior['articles'])
        self.assertEqual(result['discovery']['status'],'failed')
        self.assertFalse(result['discovery']['noNewItems'])
        self.assertEqual(result['discovery']['lastSuccessfulAt'],prior['discovery']['lastSuccessfulAt'])
    def test_retained_headline_strips_forged_official_and_investment_fields(self):
        prior=self.run_collect()
        poisoned=copy.deepcopy(prior)
        poisoned['articles'][0].update({
            'verifiedOfficial':True, 'importance':'high',
            'summary':'BUY NOW', 'summaryKind':'verified-analysis',
            'priceTarget':9999, 'classification':{'rule':'official-results'},
        })
        def blocked(_):raise ValueError('offline')
        result=self.run_collect(poisoned,blocked)
        self.assertEqual(result['articles'],prior['articles'])
        self.assertNotIn('verifiedOfficial',result['articles'][0])
        self.assertNotIn('priceTarget',result['articles'][0])
        self.assertEqual(result['articles'][0]['summaryKind'],'metadata-only')

    def test_rejects_forged_persisted_article_identity_and_links(self):
        prior=self.run_collect()
        def blocked(_):raise ValueError('offline')
        for field,value in (
            ('id','article:'+'0'*32),
            ('sourceId','sec-submissions:candidate-nebius'),
            ('discoveryProvider','sec-submissions'),
            ('sourceUrl','javascript:alert(1)'),
            ('headline','Unrelated stock upgrade'),
            ('publishedAt','2026-10-18T10:00:00-forged'),
            ('collectedAt','2026-10-18T12:00:00'),
        ):
            poisoned=copy.deepcopy(prior)
            poisoned['articles'][0][field]=value
            with self.subTest(field=field):
                result=self.run_collect(poisoned,blocked)
                self.assertEqual(result['articles'],[])

    def test_rejects_extra_persisted_article_with_valid_looking_id(self):
        prior=self.run_collect()
        injected=copy.deepcopy(prior['articles'][0])
        injected['id']='article:'+'f'*32
        injected['verifiedOfficial']=True
        poisoned=copy.deepcopy(prior)
        poisoned['articles'].append(injected)
        def blocked(_):raise ValueError('offline')
        self.assertEqual(self.run_collect(poisoned,blocked)['articles'],prior['articles'])

    def test_partial_failure(self):
        self.registry['companies'].append(copy.deepcopy(self.registry['companies'][0]))
        self.registry['companies'][1]['id']='other-company'
        self.registry['companies'][1]['query']='other'
        def getter(url):
            if 'other' in url: raise ValueError('blocked')
            return rss()
        result=self.run_collect(getter=getter)
        self.assertEqual(result['discovery']['status'],'partial')
        self.assertIsNone(result['discovery']['lastSuccessfulAt'])
    def test_malformed_and_entities(self):
        for body in (b'<html>blocked</html>',b'<rss>',b'<!DOCTYPE rss><rss/>'):
            with self.assertRaises(Exception):parse_google(body)
        result=self.run_collect(getter=lambda _:b'<html>blocked</html>')
        self.assertEqual(result['discovery']['sources'][0]['status'],'failed')
    def test_zero_is_success_distinct_from_failure(self):
        result=self.run_collect(getter=lambda _:b'<rss><channel/></rss>')
        self.assertEqual(result['discovery']['sources'][0]['status'],'zero-results')
        self.assertTrue(result['discovery']['noNewItems'])
    def test_redirect_targets(self):
        self.assertTrue(allowed(endpoint('google-news',self.registry['companies'][0])))
        for url in ('https://news.google.com.evil.test/rss/search','http://news.google.com/rss/search','https://127.0.0.1/rss/search','https://news.google.com/articles/x','https://user:pass@news.google.com/rss/search'):
            self.assertFalse(allowed(url))
    def test_no_ci_k_required(self):
        self.assertNotIn('cik',self.registry['companies'][0])
        self.assertEqual(len(self.run_collect()['articles']),1)
    def test_outside_window_filtered(self):
        result=self.run_collect(getter=lambda _:rss(date='Sun, 01 Jun 2025 10:00:00 GMT'))
        self.assertEqual(result['articles'],[])

if __name__=='__main__':unittest.main()
