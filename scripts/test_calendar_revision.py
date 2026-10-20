import copy
import unittest
from earnings import collect_calendar

class CalendarRevisionTests(unittest.TestCase):
    def test_newer_manual_review_survives_unavailable_source_and_preserves_newer_live_review(self):
        event={'period':'Q3 2026','date':'2026-11-03','status':'confirmed','eventKind':'results-date','verifiedAt':'2026-10-20','sourceUrl':'https://example.com/release','verificationMethod':'reviewed'}
        company={'securityId':'test','name':'Test','event':event,'indexUrl':None,'allowedHosts':[]}
        previous={'events':[dict(event,securityId='test',name='Test',date=None,status='unannounced',verifiedAt=None)]}
        result=collect_calendar({'companies':[company]},previous,'2026-10-20T10:00:00+00:00',pause=lambda _:None)
        self.assertEqual(result['events'][0]['date'],'2026-11-03')
        newer=copy.deepcopy(result);newer['events'][0].update(date='2026-11-04',verifiedAt='2026-10-21')
        again=collect_calendar({'companies':[company]},newer,'2026-10-21T10:00:00+00:00',pause=lambda _:None)
        self.assertEqual(again['events'][0]['date'],'2026-11-04')
