"""Free schedule admission and budget notices; no secrets, approvals or API calls."""
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from pulse_ai_cost_guard import used_in_month,validate_ledger
ROOT=Path(__file__).resolve().parent.parent

def admission(policy,queue,now):
 if (not isinstance(policy,dict) or policy.get('version')!=1
     or not isinstance(policy.get('activeMonths'),list)
     or len(policy['activeMonths'])>24
     or any(not isinstance(m,str) or not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',m) for m in policy['activeMonths'])
     or len(set(policy['activeMonths']))!=len(policy['activeMonths'])):
  raise ValueError('Invalid active-month policy')
 month=dt.datetime.fromisoformat(now.replace('Z','+00:00')).astimezone(dt.timezone.utc).strftime('%Y-%m')
 if month not in policy['activeMonths']:return {'eligible':False,'reason':'inactive-month','month':month}
 if not isinstance(queue,dict) or not isinstance(queue.get('jobs'),list) or not isinstance(queue.get('latestByCompany'),dict):
  raise ValueError('Invalid authoritative queue')
 ready=any(j.get('status')=='queued' and queue['latestByCompany'].get(j.get('companyId'))==j.get('id') for j in queue['jobs'])
 return {'eligible':ready,'reason':'queued-work' if ready else 'no-queued-work','month':month}

def budget_notice(ledger,month):
 total=used_in_month(validate_ledger(ledger),month)
 level='blocked' if total>=9 else 'warning-8' if total>=8 else 'warning-5' if total>=5 else 'within-budget'
 return {'month':month,'recordedAndReservedUsd':str(total),'level':level,
         'notice':'Local estimate including holds; provider billing is authoritative.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--state-dir',required=True);a=p.parse_args();state=Path(a.state_dir)
 queue=json.loads((state/'public/data/ai-analysis-queue.json').read_text())
 result=admission(json.loads((ROOT/'config/pulse-ai-policy.json').read_text()),queue,dt.datetime.now(dt.timezone.utc).isoformat())
 ledger=state/'public/data/ai-cost-ledger.json'
 result['budget']=budget_notice(json.loads(ledger.read_text()) if ledger.exists() else {'version':1,'calls':[],'holds':[]},result['month'])
 if result['budget']['level']=='blocked':result.update(eligible=False,reason='monthly-budget')
 if os.getenv('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('eligible='+str(result['eligible']).lower()+'\n')
 if os.getenv('GITHUB_STEP_SUMMARY'):
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('PULSE schedule admission and budget: '+json.dumps(result)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
