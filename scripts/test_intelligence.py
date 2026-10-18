import copy
import datetime as dt
import json
import unittest
from pathlib import Path
from build_intelligence import window,within,make_briefing
from rating import rate,group_events
from earnings import Page,parse_release,collect_calendar
from notifications import load_config,plan,digest,is_quiet,BASE

NOW='2026-10-18T12:00:00+00:00'
TOPIC='test_only_not_a_real_channel_123456789'

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.company=json.loads(Path('public/data/news-registry.json').read_text(encoding='utf-8'))['companies'][0]
        self.item={'id':'test-fixture','securityId':self.company['id'],'company':'Nebius','headline':'Nebius announces financial results','publisher':'Reuters','sourceUrl':'https://news.google.com/rss/articles/test-fixture','sourceId':'google-news:test','publishedAt':NOW,'collectedAt':NOW,'classification':{}}
    def test_title_only_never_high_and_separate_dimensions(self):
        r=rate(self.item,self.company)
        self.assertEqual(r['level'],'medium');self.assertEqual(r['basis'],'headline-only')
        self.assertEqual(r['sourceAuthority'],'attributed-editorial');self.assertEqual(r['independentConfirmations'],0)
    def test_opinion_price_target_is_low(self):
        self.item['headline']='Nebius price target raised despite financing concerns'
        self.assertEqual(rate(self.item,self.company)['level'],'low')
    def test_shareholder_purchase_not_company_acquisition(self):
        self.item['headline']='Test Fund Acquires 61,565 Shares of Nebius'
        r=rate(self.item,self.company);self.assertEqual(r['level'],'low');self.assertEqual(r['eventKind'],'investor-position')
    def test_future_earnings_not_actual_results(self):
        self.item['headline']='Nebius to Report Third Quarter Financial Results'
        r=rate(self.item,self.company);self.assertEqual(r['eventKind'],'results-schedule');self.assertEqual(r['level'],'low')
    def test_wrong_company_is_rejected(self):
        self.item['headline']='Other company financial results'
        r=rate(self.item,self.company);self.assertEqual(r['companyRelevance'],'rejected');self.assertEqual(r['eventScore'],0)
    def test_official_periodic_filing_has_evidence_gate(self):
        self.item.update(sourceId='sec-test',sourceUrl='https://www.sec.gov/Archives/test',headline='Quarterly report',classification={'rule':'periodic-report-v1'})
        r=rate(self.item,self.company);self.assertEqual(r['level'],'high');self.assertTrue(r['verifiedOfficial'])
    def test_syndication_is_not_independent_confirmation(self):
        a=self.item;b={**a,'id':'second-fixture','publisher':'Copy Site'}
        groups=group_events([a,b],{a['id']:rate(a,self.company),b['id']:rate(b,self.company)})
        self.assertEqual(len(groups),1);self.assertEqual(groups[0]['independentConfirmations'],0)

class DailyWindowTests(unittest.TestCase):
    def test_fixed_boundary_when_late_or_weekend(self):
        for now in ['2026-10-18T16:00:00+00:00','2026-10-17T12:00:00+00:00']:
            w=window(now);self.assertEqual((dt.datetime.fromisoformat(w['endAt'])-dt.datetime.fromisoformat(w['startAt'])).total_seconds(),86400)
            self.assertEqual(w['endAt'][11:16],'10:00')
        self.assertEqual(window('2026-10-18T08:00:00+00:00')['date'],'2026-10-17')
    def test_dst_is_24_elapsed_hours_and_13_local(self):
        for now in ['2026-03-27T14:00:00+00:00','2026-10-25T14:00:00+00:00']:
            w=window(now);self.assertEqual((dt.datetime.fromisoformat(w['endAt'])-dt.datetime.fromisoformat(w['startAt'])).total_seconds(),86400)
            self.assertTrue(w['endAt'].endswith('+00:00'))
        self.assertIn('T11:00',window('2026-10-25T14:00:00+00:00')['endAt'])
    def test_undated_and_collection_time_not_window_evidence(self):
        w=window(NOW)
        self.assertFalse(within({'publishedAt':None,'collectedAt':NOW},w))
        self.assertFalse(within({'publishedAt':w['endAt']},w))
        self.assertTrue(within({'publishedAt':w['startAt']},w))
    def test_published_briefing_is_idempotent(self):
        b={**window(NOW),'generatedAt':NOW}
        self.assertEqual(make_briefing({}, {'industries':{'config':{'version':1}}}, NOW, [b]),[b])

class CalendarTests(unittest.TestCase):
    def setUp(self):self.company={'securityId':'test-co','name':'Test Company','aliases':['Test Company'],'indexUrl':'https://example.org/news','allowedHosts':['example.org'],'event':{'period':'Q3 2026','date':'2026-10-21','time':None,'timeZone':None,'timing':None,'call':None,'sourceUrl':'https://example.org/release','status':'confirmed','eventKind':'results-date','verifiedAt':'2026-10-18','verificationMethod':'TEST FIXTURE'}}
    def page(self,title,text):
        p=Page();p.feed('<h1>'+title+'</h1><p>'+text+'</p>');return p
    def test_future_date_is_not_results_publication(self):
        p=self.page('Test Company to Report Third Quarter 2026 Results','The company intends to release financial results for the quarter ended September 30, 2026 on November 12, 2026 after market close.')
        r=parse_release(p,'https://example.org/release',self.company,NOW)
        self.assertEqual(r['kind'],'date-announced');self.assertEqual(r['date'],'2026-11-12');self.assertIsNone(r['time'])
    def test_unrelated_investor_meeting_date_not_used(self):
        p=self.page('Test Company Announces Timing of Third Quarter 2026 Earnings; Meeting on December 10, 2026','Test Company plans to announce financial results before market opens on Thursday, October 29, 2026.')
        r=parse_release(p,'https://example.org/release',self.company,NOW);self.assertEqual(r['date'],'2026-10-29')
    def test_call_time_not_report_time(self):
        p=self.page('Test Company to Report First Quarter 2027 Results on October 29, 2026','The company will hold its earnings conference call on Thursday, October 29, 2026 at 1:30 p.m. Pacific Time.')
        r=parse_release(p,'https://example.org/release',self.company,NOW)
        self.assertIsNone(r['time']);self.assertEqual(r['eventKind'],'earnings-call')
    def test_actual_release_missing_date_not_invented(self):
        p=self.page('Test Company Reports Third Quarter 2026 Financial Results','Results for the quarter.')
        r=parse_release(p,'https://example.org/release',self.company,NOW)
        self.assertEqual(r['kind'],'results-published');self.assertIsNone(r['publishedAt'])
    def test_official_meta_title_fallback(self):
        p=Page();p.feed('<meta property="og:title" content="Test Company Reports Third Quarter 2026 Financial Results"><h3>Financial results</h3>')
        r=parse_release(p,'https://example.org/release',self.company,NOW)
        self.assertEqual(r['kind'],'results-published');self.assertIsNone(r['publishedAt'])
    def test_blocked_source_preserves_known_date(self):
        def blocked(*_):raise ValueError('HTTP 403')
        x=collect_calendar({'companies':[self.company]}, {},NOW,blocked,lambda _:None)
        self.assertEqual(x['events'][0]['date'],'2026-10-21');self.assertEqual(x['sources'][0]['status'],'failed')
    def test_changed_date_retains_period_identity(self):
        old=collect_calendar({'companies':[self.company]}, {},NOW,lambda *_:self.page('',''),lambda _:None)
        def getter(url,*_):
            if url.endswith('/news'):
                p=self.page('','');p.links=[('/release','Test Company Results')];return p
            return self.page('Test Company to Report Third Quarter 2026 Results','We will release financial results on October 22, 2026.')
        new=collect_calendar({'companies':[self.company]},old,NOW,getter,lambda _:None)
        self.assertEqual(old['events'][0]['id'],new['events'][0]['id']);self.assertNotEqual(old['events'][0]['revision'],new['events'][0]['revision'])

class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.c={'enabled':True,'companyIds':['test-co'],'types':['daily','high','reminder','results','schedule-change'],'quietHours':{'start':22,'end':7},'urgentOverride':False,'reminderDays':[3,1]}
        self.event={'id':'earnings:test:Q3','revision':'rev-a','securityId':'test-co','name':'Test Company','status':'confirmed','date':'2026-10-21','period':'Q3 2026'}
        self.feed={'news':[],'articles':[],'intelligence':{'calendar':{'events':[self.event],'releases':[]},'dailyBriefings':[],'ratings':{},'eventGroups':[]}}
        self.ledger={'version':1,'channelTag':digest(TOPIC,'channel-version-3'),'attempted':{},'reminded':{},'baseline':[]}
    def test_private_config_validation(self):
        self.assertIsNone(load_config('',TOPIC,['test-co']))
        self.assertIsNone(load_config(json.dumps(self.c),'guessable',['test-co']))
        with self.assertRaises(ValueError):load_config(json.dumps({**self.c,'companyIds':['wrong']}),TOPIC,['test-co'])
    def test_bootstrap_suppresses_history_but_explicit_test_works(self):
        ledger,messages,fresh=plan(self.feed,NOW,self.c,TOPIC,{})
        self.assertTrue(fresh);self.assertEqual(messages,[])
        _,messages,_=plan(self.feed,NOW,self.c,TOPIC,{},'manual-test-run')
        self.assertEqual(len(messages),1);self.assertEqual(messages[0]['type'],'test')
        self.assertNotIn(TOPIC,json.dumps(ledger));self.assertNotIn('Test Company',json.dumps(ledger))
    def test_reminders_three_days_and_one_day_then_dedup(self):
        ledger,msg,_=plan(self.feed,NOW,self.c,TOPIC,copy.deepcopy(self.ledger));self.assertEqual(msg[0]['type'],'reminder')
        _,repeat,_=plan(self.feed,NOW,self.c,TOPIC,ledger);self.assertEqual(repeat,[])
        _,day_before,_=plan(self.feed,'2026-10-20T12:00:00+00:00',self.c,TOPIC,ledger);self.assertEqual(len(day_before),1)
    def test_change_notifies_only_after_prior_reminder(self):
        ledger,_,_=plan(self.feed,NOW,self.c,TOPIC,copy.deepcopy(self.ledger))
        self.event.update(revision='rev-b',date='2026-10-25')
        _,msg,_=plan(self.feed,NOW,self.c,TOPIC,ledger);self.assertEqual([m['type'] for m in msg],['schedule-change'])
        _,none,_=plan(self.feed,NOW,self.c,TOPIC,copy.deepcopy(self.ledger));self.assertEqual(none,[])
    def test_quiet_muted_and_urgent_override(self):
        self.assertTrue(is_quiet('2026-10-18T20:00:00+00:00',self.c))
        _,msg,_=plan(self.feed,NOW,{**self.c,'enabled':False},TOPIC,copy.deepcopy(self.ledger));self.assertEqual(msg,[])
    def test_actual_result_and_deeplink_are_public_only(self):
        self.feed['intelligence']['calendar']['events']=[]
        self.feed['intelligence']['calendar']['releases']=[{'id':'results:test','securityId':'test-co','name':'Test Company','verifiedOfficial':True,'firstDetectedAt':NOW,'headline':'Test Company Reports Results'}]
        ledger,msg,_=plan(self.feed,NOW,self.c,TOPIC,copy.deepcopy(self.ledger))
        self.assertEqual(msg[0]['type'],'results');self.assertTrue(msg[0]['click'].startswith(BASE+'#results='))
        _,repeat,_=plan(self.feed,NOW,self.c,TOPIC,ledger);self.assertEqual(repeat,[])

if __name__=='__main__':unittest.main()
