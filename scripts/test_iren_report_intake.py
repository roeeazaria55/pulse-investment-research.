"""IREN intake regression fixtures. The HTML body is synthetic, not issuer figures."""
import copy
import json
import unittest
from pathlib import Path
from report_intake import PILOTS, candidates, collect

COMPANY=next(c for c in json.loads(Path('public/data/official-registry.json').read_text())['companies'] if c['id']=='candidate-iren')
URL='https://rss.globenewswire.com/news-release/2026/08/27/3352401/0/en/iren-reports-fy26-results.html'
ITEM={'id':'official:iren-fixture','companyId':COMPANY['id'],'kind':'results','title':'IREN Reports FY26 Results','url':URL,'publishedDate':'2026-08-27','documentPeriod':None,'periodBasis':'unknown','lastSeenAt':'2026-10-21T00:00:00Z'}
NOW='2026-10-21T13:00:00Z'
LATER='2026-10-21T14:00:00Z'
HTML=b'<html><h1>IREN Reports FY26 Results</h1><p>This synthetic test fixture exercises issuer identity and financial-table extraction only. It contains no actual financial figures.</p><table><tr><th>Metric</th><th>Test marker</th></tr><tr><td>Revenue</td><td>not an issuer value</td></tr></table></html>'


class IrenIntakeTests(unittest.TestCase):
    def collect(self, snapshot=None, previous=None, fetcher=None, **kwargs):
        return collect(snapshot if snapshot is not None else {'items':[ITEM]}, {'companies':[COMPANY]}, previous or {}, NOW, fetcher=fetcher or (lambda url,c:(HTML,'text/html',url)), **kwargs)

    def test_registered_official_sources_and_pilot_membership(self):
        self.assertIn(COMPANY['id'],PILOTS)
        self.assertTrue(any(s.get('kind')=='issuer-distributed' for s in COMPANY['sources']))
        self.assertIn(URL.split('/')[2],COMPANY['allowedHosts'])
        self.assertEqual(candidates({'items':[ITEM]},COMPANY),[ITEM])

    def test_fy26_and_fy2026_are_candidates_without_invented_accounting_dates(self):
        for title in ['IREN Reports FY26 Results','IREN Reports FY2026 Results']:
            item={**ITEM,'title':title}
            result=self.collect({'items':[item]})
            self.assertEqual(result['sources'][0]['status'],'ok')
            document=result['documents'][0]
            self.assertEqual(document['url'],URL)
            self.assertIsNone(document['documentPeriod'])
            self.assertEqual(document['facts'],[])
            self.assertEqual(document['reviewStatus'],'pending-review')
            self.assertEqual(document['tableCount'],1)

    def test_fiscal_annual_results_rank_after_same_year_q3_and_before_older_year(self):
        items=[{**ITEM,'title':t} for t in ['IREN Q3 FY26 Results Conference Call','IREN Reports FY25 Results','IREN Reports FY26 Results']]
        self.assertEqual([i['title'] for i in candidates({'items':items},COMPANY)],['IREN Reports FY26 Results','IREN Q3 FY26 Results Conference Call','IREN Reports FY25 Results'])

    def test_schedules_operational_releases_and_other_issuers_are_excluded(self):
        items=[{**ITEM,'kind':'schedule','title':'IREN to Release FY26 Results on August 27, 2026'},
               {**ITEM,'kind':'release','title':'IREN FY26 Cloud Contract'},
               {**ITEM,'companyId':'candidate-nebius'},
               {**ITEM,'url':'https://evil.test/news-release/iren-results'}]
        self.assertEqual(candidates({'items':items},COMPANY),[])

    def test_unavailable_report_is_failure_not_no_candidates_or_unpublished(self):
        def unavailable(*_):raise ValueError('HTTP 403: Forbidden')
        result=self.collect(fetcher=unavailable)
        self.assertEqual(result['documents'],[])
        self.assertEqual(result['sources'][0]['status'],'failed')
        self.assertEqual(result['sources'][0]['error'],'HTTP 403: Forbidden')

    def test_failed_refresh_preserves_original_iren_evidence(self):
        first=self.collect();before=copy.deepcopy(first)
        def unavailable(*_):raise ValueError('HTTP 503: Service Unavailable')
        result=collect({'items':[ITEM]},{'companies':[COMPANY]},first,LATER,fetcher=unavailable)
        old,new=first['documents'][0],result['documents'][0]
        self.assertEqual(new['sha256'],old['sha256'])
        self.assertEqual(new['lastSuccessfulAt'],NOW)
        self.assertEqual(new['lastAttemptAt'],LATER)
        self.assertEqual(new['tables'],old['tables'])
        self.assertEqual(result['sources'][0]['status'],'failed')
        self.assertEqual(first,before)

    def test_failed_discovery_without_records_is_not_no_candidates(self):
        snapshot={'items':[],'sources':[{'companyId':COMPANY['id'],'status':'failed','error':'HTTP 403'}]}
        result=self.collect(snapshot)
        self.assertEqual(result['sources'][0]['status'],'failed')
        self.assertIn('discovery failed',result['sources'][0]['error'])
        self.assertIn('publication status unknown',result['sources'][0]['error'])

    def test_successful_or_unknown_discovery_without_records_makes_no_publication_claim(self):
        for sources in [[],[{'companyId':COMPANY['id'],'status':'ok','error':None}]]:
            result=self.collect({'items':[],'sources':sources})
            self.assertEqual(result['sources'][0]['status'],'no-candidates')
            self.assertEqual(result['documents'],[])
            self.assertIn('Failure is not evidence that no report exists',result['notice'])

    def test_retained_candidate_can_still_be_read_after_discovery_failure(self):
        snapshot={'items':[ITEM],'sources':[{'companyId':COMPANY['id'],'status':'failed','error':'HTTP 403'}]}
        self.assertEqual(self.collect(snapshot)['sources'][0]['status'],'ok')

    def test_budget_deferral_records_iren_without_claiming_an_absent_report(self):
        def forbidden(*_):self.fail('Budget exhausted: network must not be called')
        result=self.collect(fetcher=forbidden,limit=0)
        self.assertEqual(result['sources'][0]['companyId'],COMPANY['id'])
        self.assertEqual(result['sources'][0]['status'],'deferred')


if __name__=='__main__':unittest.main()
