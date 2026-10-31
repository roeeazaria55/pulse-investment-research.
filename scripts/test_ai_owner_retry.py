"""A single explicit retry preserves original billing and cannot chain retries."""
import copy
import unittest
from pulse_ai_cost_guard import reserve, record_call, preflight, validate_ledger, used_in_month

NOW='2026-10-31T00:00:00Z'
SHA='a'*64
MODEL='gpt-6.1-sol'
class OwnerRetryTests(unittest.TestCase):
 def original(self):
  reserved,hold=reserve({'version':1,'calls':[],'holds':[]},'NBIS',SHA,MODEL,NOW,10000,6000)
  billed,receipt=record_call(reserved,'NBIS',SHA,MODEL,NOW,{'input_tokens':7983,'output_tokens':6000})
  return reserved,billed,receipt
 def test_one_retry_preserves_both_costs_and_blocks_replay(self):
  _,billed,receipt=self.original();before=copy.deepcopy(billed)
  reserved,hold=reserve(billed,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=receipt['id'])
  self.assertEqual(reserved['calls'],before['calls'])
  self.assertEqual(hold['maxUsd'],'0.52')
  self.assertNotEqual(hold['id'],receipt['id'])
  self.assertFalse(preflight(reserved,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=receipt['id'])['allowed'])
  done,second=record_call(reserved,'NBIS',SHA,MODEL,NOW,{'input_tokens':10000,'output_tokens':10000},retry_of=receipt['id'])
  self.assertEqual(len(done['calls']),2)
  self.assertEqual(str(used_in_month(done,'2026-10')),'0.20')
  self.assertFalse(preflight(done,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=receipt['id'])['allowed'])
  with self.assertRaises(ValueError):
   reserve(done,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=second['id'])
 def test_unsettled_or_changed_source_cannot_retry(self):
  reserved,billed,receipt=self.original()
  for ledger,ticker,sha in [(reserved,'NBIS',SHA),(billed,'META',SHA),(billed,'NBIS','b'*64)]:
   with self.subTest(ticker=ticker,sha=sha),self.assertRaises(ValueError):
    reserve(ledger,ticker,sha,MODEL,NOW,100000,32000,retry_of=receipt['id'])
 def test_runner_consumes_precommitted_retry_and_records_failed_output(self):
  import tempfile,json,contextlib,io
  from pathlib import Path
  from unittest.mock import patch
  import run_optional_ai_review as runner
  _,billed,receipt=self.original()
  reserved,_=reserve(billed,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=receipt['id'])
  with tempfile.TemporaryDirectory() as d:
   ledger=Path(d)/'ledger.json';target=Path(d)/'review.json'
   ledger.write_text(json.dumps(reserved))
   response={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
             'usage':{'input_tokens':10000,'output_tokens':32000}}
   with patch.object(runner,'urlopen') as network,contextlib.redirect_stdout(io.StringIO()):
    network.return_value.__enter__.return_value.read.return_value=json.dumps(response).encode()
    with self.assertRaisesRegex(ValueError,'max_output_tokens'):
     runner.run_paid_review('NBIS',{'contentSha256':SHA},'{}',MODEL,'fake-key',target,ledger,
                            reservation_precommitted=True,retry_of=receipt['id'])
    self.assertEqual(network.call_count,1)
   final=runner.read_ledger(ledger)
   self.assertEqual(final['calls'][0],receipt)
   self.assertEqual(final['calls'][1]['retryOf'],receipt['id'])
   self.assertFalse(final['holds']);self.assertFalse(target.exists())
 def test_retry_parent_cannot_be_removed(self):
  _,billed,receipt=self.original()
  reserved,_=reserve(billed,'NBIS',SHA,MODEL,NOW,100000,32000,retry_of=receipt['id'])
  reserved['calls']=[]
  with self.assertRaises(ValueError):validate_ledger(reserved)
if __name__=='__main__':unittest.main()
