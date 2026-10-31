import unittest
from pulse_ai_schedule import admission,budget_notice
from pulse_ai_cost_guard import packet_key
class ScheduleTests(unittest.TestCase):
 def queue(self,status='queued'):
  return {'jobs':[{'id':'job','companyId':'company','status':status}],'latestByCompany':{'company':'job'}}
 def test_inactive_and_empty_queues_never_request_paid_approval(self):
  self.assertFalse(admission({'version':1,'activeMonths':[]},self.queue(),'2026-10-31T23:59:00Z')['eligible'])
  p={'version':1,'activeMonths':['2026-11']}
  self.assertFalse(admission(p,self.queue(),'2026-10-31T23:59:00Z')['eligible'])
  self.assertTrue(admission(p,self.queue(),'2026-11-01T00:00:00Z')['eligible'])
  self.assertFalse(admission(p,self.queue('failed'),'2026-11-01T00:00:00Z')['eligible'])
  self.assertFalse(admission(p,self.queue('pending-review'),'2026-11-01T00:00:00Z')['eligible'])
 def test_malformed_policy_is_refused(self):
  for months in [['2026-13'],['2026-11','2026-11'],['*']]:
   with self.assertRaises(ValueError):admission({'version':1,'activeMonths':months},self.queue(),'2026-11-01T00:00:00Z')
 def test_budget_alerts_include_outstanding_reservations(self):
  for amount,level in [('4.99','within-budget'),('5.00','warning-5'),('8.00','warning-8'),('9.00','blocked')]:
   ledger={'version':1,'calls':[],'holds':[{'id':packet_key('SMCI','a'*64,'gpt-6.1-sol'),'ticker':'SMCI','model':'gpt-6.1-sol','packetSha256':'a'*64,'heldAt':'2026-11-01T00:00:00Z','maxUsd':amount}]}
   self.assertEqual(budget_notice(ledger,'2026-11')['level'],level)
if __name__=='__main__':unittest.main()
