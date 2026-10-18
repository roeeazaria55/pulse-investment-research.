"""Private configuration, public-only messages, intent persisted before one send attempt."""
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

BASE='https://roeeazaria55.github.io/pulse-investment-research./'
TYPES={'daily','high','reminder','results','schedule-change'}
def load_config(raw,topic,company_ids):
    if not topic or not re.fullmatch(r'[A-Za-z0-9_-]{24,64}',topic):return None
    if not raw:return None
    c=json.loads(raw)
    if not isinstance(c,dict) or set(c)-{'enabled','companyIds','types','quietHours','urgentOverride','reminderDays'}:raise ValueError('Invalid private notification settings')
    if not isinstance(c.get('enabled'),bool) or not isinstance(c.get('urgentOverride',False),bool):raise ValueError('Invalid enable/override flags')
    if not isinstance(c.get('companyIds'),list) or not set(c['companyIds'])<=set(company_ids):raise ValueError('Unknown notification company')
    if not isinstance(c.get('types'),list) or not set(c['types'])<=TYPES:raise ValueError('Unknown notification types')
    quiet=c.get('quietHours',{'start':22,'end':7})
    if not isinstance(quiet,dict) or set(quiet)!={'start','end'} or any(type(quiet[k]) is not int or not 0<=quiet[k]<=23 for k in quiet):raise ValueError('Invalid quiet hours')
    leads=c.get('reminderDays',[3,1])
    if not isinstance(leads,list) or len(leads)>7 or any(type(x) is not int or not 0<=x<=14 for x in leads):raise ValueError('Invalid reminder days')
    return {**c,'quietHours':quiet,'reminderDays':sorted(set(leads),reverse=True)}

def is_quiet(now,c):
    hour=dt.datetime.fromisoformat(now).astimezone(ZoneInfo('Asia/Jerusalem')).hour
    start,end=c['quietHours']['start'],c['quietHours']['end']
    return False if start==end else start<=hour<end if start<end else hour>=start or hour<end

def digest(topic,key):return hmac.new(topic.encode(),key.encode(),hashlib.sha256).hexdigest()
def candidates(feed,now,c,ledger,topic):
    intel=feed.get('intelligence',{});out=[];ids=set(c['companyIds'])
    local=dt.datetime.fromisoformat(now).astimezone(ZoneInfo('Asia/Jerusalem'))
    def add(kind,key,title,message,link,urgent=False):out.append({'type':kind,'key':digest(topic,kind+':'+key),'title':title,'message':message[:1500],'click':BASE+link,'urgent':urgent})
    brief=(intel.get('dailyBriefings') or [None])[0]
    if brief and any(x['securityId'] in ids for x in brief['companies']):
        add('daily',brief['id'],'PULSE — התדריך היומי מוכן','חלון 24 שעות עד 13:00 שעון ישראל. תדריך מטא־נתונים; בדקו מקורות וכיסוי.', '#briefing='+brief['date'])
    for n in [*feed.get('articles',[]),*feed.get('news',[])]:
        r=intel.get('ratings',{}).get(n['id'],{})
        if n.get('securityId') not in ids or r.get('level')!='high' or not r.get('verifiedOfficial'):continue
        if (dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(n['collectedAt'])).total_seconds()>86400:continue
        event=next((g['id'] for g in intel['eventGroups'] if n['id'] in g['itemIds']),n['id'])
        add('high',event,'PULSE — '+n['company'],n['headline']+'\n'+r['why'],'#news='+urllib_quote(n['id']),True)
    for e in intel.get('calendar',{}).get('events',[]):
        if e['securityId'] not in ids or e['status']!='confirmed' or not e['date']:continue
        identity=digest(topic,'calendar:'+e['id'])
        delta=(dt.date.fromisoformat(e['date'])-local.date()).days
        if delta in c['reminderDays'] and local.hour>=9:
            add('reminder',e['id']+':'+e['revision']+':'+str(delta),'PULSE — '+e['name'],f"תזכורת: {e['period']} בתאריך {e['date']}, בעוד {delta} ימים. המועד מבוסס על הודעה רשמית; פרסום תוצאות ושיחה הם אירועים נפרדים.",'#earnings='+urllib_quote(e['id']))
        previous_revision=ledger.get('reminded',{}).get(identity)
        if previous_revision and previous_revision!=e['revision']:
            add('schedule-change',e['id']+':'+e['revision'],'PULSE — שינוי מועד '+e['name'],f"מועד שאושר קודם השתנה ל־{e['date']}. בדקו את ההודעה הרשמית.",'#earnings='+urllib_quote(e['id']))
    for r in intel.get('calendar',{}).get('releases',[]):
        if r['securityId'] not in ids or not r['verifiedOfficial']:continue
        if (dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(r['firstDetectedAt'])).total_seconds()>86400:continue
        add('results',r['id'],'PULSE — תוצאות '+r['name'],r['headline']+'\nזוהה פרסום רשמי; אין זו הודעה על מועד עתידי.','#results='+urllib_quote(r['id']),True)
    return out

def urllib_quote(value):
    import urllib.parse
    return urllib.parse.quote(value,safe='')

def plan(feed,now,c,topic,ledger,test_id=None):
    tag=digest(topic,'channel-version-3');fresh=ledger.get('channelTag')!=tag
    ledger=ledger if not fresh else {'version':1,'channelTag':tag,'attempted':{},'reminded':{},'baseline':[]}
    events=candidates(feed,now,c,ledger,topic)
    # A missing/evicted ledger or a new channel establishes a baseline and sends
    # no collected history. Only an explicit test may send on bootstrap.
    if fresh:
        ledger['baseline']=[e['key'] for e in events]
    selected=[]
    for e in events:
        if fresh or e['key'] in ledger['attempted'] or e['key'] in ledger.get('baseline',[]) or e['type'] not in c['types'] or not c['enabled']:continue
        if is_quiet(now,c) and not (c.get('urgentOverride') and e['urgent']):continue
        selected.append(e)
    if test_id:
        key=digest(topic,'test:'+test_id)
        if key not in ledger['attempted']:
            selected=[{'type':'test','key':key,'title':'PULSE — בדיקת חיבור','message':'התראת ניסיון עם מידע ציבורי בלבד. בדקו קבלה בטלפון נעול כש־PULSE סגור, ואז הקישו לפתיחת PULSE. אישור מהשרת אינו הוכחת קבלה בטלפון.','click':BASE+'#notifications=setup','urgent':False}]
    # Reserve send intents BEFORE network access. No automatic resend after an
    # ambiguous timeout. A crash can lose a message; it cannot safely promise exactly-once delivery.
    today=dt.datetime.fromisoformat(now).astimezone(ZoneInfo('Asia/Jerusalem')).date()
    already_today=sum(dt.datetime.fromisoformat(v).astimezone(ZoneInfo('Asia/Jerusalem')).date()==today for v in ledger['attempted'].values())
    selected=selected[:min(10,max(0,40-already_today))]
    for e in selected:ledger['attempted'][e['key']]=now
    for e in feed.get('intelligence',{}).get('calendar',{}).get('events',[]):
        key=digest(topic,'calendar:'+e['id'])
        if any(x['type']=='reminder' and x['click'].endswith(urllib_quote(e['id'])) for x in selected):ledger['reminded'][key]=e['revision']
    cutoff=dt.datetime.fromisoformat(now)-dt.timedelta(days=90)
    ledger['attempted']={k:v for k,v in ledger['attempted'].items() if dt.datetime.fromisoformat(v)>=cutoff}
    if len(ledger['attempted'])>10000:raise ValueError('Notification ledger limit')
    return ledger,selected[:10],fresh

def send(messages,topic,token):
    accepted=0;failed=0
    # Exactly one transport attempt per reserved intent. Never log topic, token,
    # payload selection, raw responses or private company configuration.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise ValueError('ntfy redirects are not allowed')
    opener=urllib.request.build_opener(NoRedirect())
    for m in messages:
        body=json.dumps({'topic':topic,'sequence_id':m['key'],'title':m['title'],'message':m['message'],'click':m['click'],'priority':4 if m['urgent'] else 3,'tags':['chart_with_upwards_trend']},ensure_ascii=False).encode()
        headers={'Content-Type':'application/json','User-Agent':'PULSE/3 public notification relay'}
        if token:headers['Authorization']='Bearer '+token
        try:
            with opener.open(urllib.request.Request('https://ntfy.sh/',data=body,headers=headers,method='POST'),timeout=12) as response:
                raw=response.read(16385)
                if len(raw)>16384:raise ValueError('Response size limit')
                result=json.loads(raw)
                if response.status!=200 or result.get('event')!='message':raise ValueError('Publish not acknowledged')
                accepted+=1
        except Exception:failed+=1
    return {'acceptedByService':accepted,'failedOrUnknown':failed,'deviceReceipt':'not-verified'}

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'plan'
    topic=os.getenv('NTFY_TOPIC','');token=os.getenv('NTFY_TOKEN','')
    Path('work').mkdir(exist_ok=True)
    if mode=='plan':
        feed=json.loads(Path('public/data/feed.json').read_text(encoding='utf-8'))
        ids=[c['id'] for c in feed.get('discovery',{}).get('registry',{}).get('companies',[])]
        try:c=load_config(os.getenv('PULSE_NOTIFY_CONFIG',''),topic,ids)
        except Exception:c=None
        ready=bool(c)
        if ready:
            path=Path('work/notify-ledger.json')
            try:ledger=json.loads(path.read_text())
            except (FileNotFoundError,json.JSONDecodeError):ledger={}
            now=dt.datetime.now(dt.timezone.utc).isoformat()
            ledger,messages,bootstrap=plan(feed,now,c,topic,ledger,os.getenv('GITHUB_RUN_ID') if os.getenv('PULSE_TEST_NOTIFICATION')=='true' else None)
            path.write_text(json.dumps(ledger),encoding='utf-8')
            Path('work/ntfy-plan.json').write_text(json.dumps(messages,ensure_ascii=False),encoding='utf-8')
        else:messages=[];bootstrap=False
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('ready='+str(ready).lower()+'\n')
        print(json.dumps({'configured':ready,'plannedCount':len(messages),'bootstrap':bootstrap,'deviceReceipt':'not-verified'}))
    elif mode=='send':
        messages=json.loads(Path('work/ntfy-plan.json').read_text(encoding='utf-8'))
        report=send(messages,topic,token)
        print(json.dumps(report))
        if os.getenv('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(f"## Notification transport\n\nService acknowledgements: {report['acceptedByService']}. Failed or unknown: {report['failedOrUnknown']}. Android receipt is **not verified**. No private configuration is published.\n")
