"""Independent headline intelligence, fixed 08:00/19:00 windows, public calendar."""
import datetime as dt
import hashlib
import json
import os
import time
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo
from collect_articles import contains
from news_poc import fetch,parse_google
from earnings import collect_calendar
from rating import rate,group_events,VERSION

UTC=dt.timezone.utc
ZONE=ZoneInfo('Asia/Jerusalem')

def window(now):
    """Previous completed 08:00/19:00 Jerusalem boundary, DST-aware.

    Overnight windows may differ in UTC duration during clock changes.
    Delayed scheduled runs do not pretend to have executed at the boundary.
    """
    local=dt.datetime.fromisoformat(now).astimezone(ZONE)
    date=local.date()
    if local.hour>=19:
        hour=19
        previous=dt.datetime.combine(date,dt.time(8),ZONE)
    elif local.hour>=8:
        hour=8
        previous=dt.datetime.combine(date-dt.timedelta(days=1),dt.time(19),ZONE)
    else:
        date-=dt.timedelta(days=1)
        hour=19
        previous=dt.datetime.combine(date,dt.time(8),ZONE)
    end=dt.datetime.combine(date,dt.time(hour),ZONE)
    return {'id':f'briefing:{date.isoformat()}:{hour:02d}',
            'date':date.isoformat(),'startAt':previous.astimezone(UTC).isoformat(),
            'endAt':end.astimezone(UTC).isoformat(),
            'timezone':'Asia/Jerusalem','scheduledLocalTime':f'{hour:02d}:00'}

def within(item,win):
    stamp=item.get('publishedAt')
    if not stamp:return False
    try:return dt.datetime.fromisoformat(win['startAt'])<=dt.datetime.fromisoformat(stamp)<dt.datetime.fromisoformat(win['endAt'])
    except (ValueError,TypeError):return False

def collect_industries(config,previous,now,getter=fetch,pause=time.sleep):
    items={i['id']:i for i in previous.get('items',[])};sources=[]
    for industry in config['industries']:
        old=next((s for s in previous.get('sources',[]) if s['industryId']==industry['id']),{})
        source={'industryId':industry['id'],'provider':'google-news','lastAttemptAt':now,'lastSuccessfulAt':old.get('lastSuccessfulAt'),'status':'failed','count':0,'error':None}
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':industry['query']+' when:7d','hl':'en-US','gl':'US','ceid':'US:en'})
        source['queryUrl']=url
        try:
            candidates=parse_google(getter(url),required_term=None)
            selected=[a for a in candidates if any(contains(a['title'],t) for t in industry['terms'])]
            selected.sort(key=lambda a:a.get('publishedAt') or '',reverse=True)
            for a in selected[:12]:
                key='industry:'+hashlib.sha256((industry['id']+a['title'].rsplit(' - ',1)[0].lower()).encode()).hexdigest()[:32]
                items.setdefault(key,{'id':key,'industryId':industry['id'],'headline':a['title'],'publisher':a['publisher'],
                                     'sourceUrl':a['url'],'linkKind':'google-news-redirect','publishedAt':a['publishedAt'],'collectedAt':now})
            source.update(status='results' if selected else 'zero-results',count=min(12,len(selected)),lastSuccessfulAt=now)
        except Exception as exc:source['error']=str(exc)[:200]
        sources.append(source);pause(3)
    cutoff=dt.datetime.fromisoformat(now)-dt.timedelta(days=14)
    retained=[i for i in items.values() if not i['publishedAt'] or dt.datetime.fromisoformat(i['publishedAt'])>=cutoff]
    retained.sort(key=lambda i:i['publishedAt'] or i['collectedAt'],reverse=True)
    return {'items':retained[:200],'sources':sources,'config':config}

def make_briefing(feed,intel,now,previous):
    win=window(now)
    existing=next((b for b in previous if b['id']==win['id']),None)
    if existing and existing.get('queryVersion',1)==intel['industries']['config']['version'] and existing.get('ratingVersion',VERSION)==VERSION:
        return [existing]+[b for b in previous if b['id']!=win['id']][:29]
    articles=[*feed.get('articles',[]),*feed['news']]
    eligible=[n for n in articles if within(n,win)]
    eligible_ids={n['id'] for n in eligible}
    company_sections=[]
    for c in feed['discovery']['registry']['companies']:
        status=next((s for s in feed['discovery']['sources'] if s['securityId']==c['id']),None)
        events=[g for g in intel['eventGroups'] if g['securityId']==c['id'] and any(i in eligible_ids for i in g['itemIds'])]
        events.sort(key=lambda g:max(intel['ratings'][i]['eventScore'] for i in g['itemIds']),reverse=True)
        facts=[]
        for g in events[:8]:
            item=next(n for n in eligible if n['id'] in g['itemIds'])
            rating=intel['ratings'][item['id']]
            facts.append({'eventId':g['id'],'itemId':item['id'],'textHe':f"פורסמה כותרת בנושא {rating['eventLabel']} — מבוסס על כותרת בלבד." if rating['basis']=='headline-only' else f"פורסם מטא־נתון רשמי בנושא {rating['eventLabel']}.",
                          'originalTitle':item['headline'],'sourceUrl':item['sourceUrl'],'publishedAt':item['publishedAt'],
                          'basis':rating['basis'],'publisher':item.get('publisher') or item.get('sourceName') or 'SEC'})
        industry_ids=intel['industries']['config']['companyIndustries'].get(c['id'],[])
        industry_items=[n for n in intel['industries']['items'] if n['industryId'] in industry_ids and within(n,win)][:3]
        company_sections.append({'securityId':c['id'],'name':c['name'],'searchStatus':status['status'] if status else 'failed',
                                 'facts':facts,'undatedItemIds':[n['id'] for n in articles if n.get('securityId')==c['id'] and not n['publishedAt']][:15],
                                 'industryItemIds':[n['id'] for n in industry_items],
                                 'industryConnection':'הקשר ענפי לתחומי הפעילות שנרשמו לחברה; אירוע אצל מתחרה אינו אירוע של החברה.',
                                 'researchInterpretation':'שאלת מחקר, לא עובדה: האם ההתפתחות משנה הנחות על ביקוש, מימון, תחרות או סיכון?',
                                 'missing':['יש לקרוא את המקור המלא ולוודא נתונים והקשר.','הפיד אינו מוכיח השפעה כספית או כיוון מחיר.']})
    briefing={**win,'generatedAt':now,'firstGeneratedAt':existing.get('firstGeneratedAt',existing['generatedAt']) if existing else now,
              'revision':existing.get('revision',0)+1 if existing else 0,'queryVersion':intel['industries']['config']['version'],
              'kind':'metadata-template-not-ai','ratingVersion':VERSION,'companies':company_sections,
              'companySearchesSuccessful':sum(s['status']!='failed' for s in feed['discovery']['sources']),
              'industrySearchesSuccessful':sum(s['status']!='failed' for s in intel['industries']['sources']),
              'summaryStatus':intel['summary']['status'],
              'notice':'תדריך מטא־נתונים בעברית. אין סיכום AI מאומת של כתבות מלאות. חלון הפרסום קבוע גם כאשר ההפקה מתעכבת.'}
    return [briefing]+[b for b in previous if b['id']!=win['id']][:29]

def build(feed,previous,industry_config,earnings_registry,now,industry_getter=fetch,ir_getter=None,pause=time.sleep):
    old=previous.get('intelligence',{})
    industries=collect_industries(industry_config,old.get('industries',{}),now,industry_getter,pause)
    calendar=collect_calendar(earnings_registry,old.get('calendar',{}),now,**({'getter':ir_getter} if ir_getter else {}),pause=pause)
    companies={c['id']:c for c in feed['discovery']['registry']['companies']}
    items=[*feed.get('articles',[]),*feed['news']]
    ratings={n['id']:rate(n,companies.get(n.get('securityId'))) for n in items}
    for n in items:
        r=ratings[n['id']];n['importance']=r['level'];n['classification']={'rule':VERSION+':'+r['eventKind'],'reason':r['why']}
    intel={'version':1,'generatedAt':now,'ratingVersion':VERSION,'ratings':ratings,'eventGroups':group_events(items,ratings),
           'industries':industries,'calendar':calendar,
           'summary':json.loads(Path('public/data/summary-feasibility.json').read_text(encoding='utf-8'))['publicStatus'],
           'notificationNotice':'הגדרות התראות נשמרות ב־GitHub Secrets בלבד. רשימת המעקב המקומית אינה מסונכרנת להתראות. קבלה באנדרואיד טרם אומתה.'}
    intel['dailyBriefings']=make_briefing(feed,intel,now,old.get('dailyBriefings',[]))
    return intel

if __name__=='__main__':
    def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
    feed=load('public/data/feed.json');previous=load('work/previous-feed.json')
    now=dt.datetime.now(UTC).isoformat()
    feed['intelligence']=build(feed,previous,load('public/data/industry-registry.json'),load('public/data/earnings-registry.json'),now)
    # Write only the fixed public feed after construction; CI schema validation follows.
    path=Path('public/data/feed.json.tmp');path.write_text(json.dumps(feed,ensure_ascii=False,indent=2),encoding='utf-8');path.replace('public/data/feed.json')
    print(json.dumps({'ratingVersion':VERSION,'industrySources':feed['intelligence']['industries']['sources'],
                      'calendarSources':feed['intelligence']['calendar']['sources'],
                      'dailyWindow':{k:v for k,v in feed['intelligence']['dailyBriefings'][0].items() if k in ('id','startAt','endAt','generatedAt')}}))
