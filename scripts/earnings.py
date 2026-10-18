"""Bounded public IR metadata checks. No article text is saved or executed."""
import copy
import datetime as dt
import hashlib
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

class Page(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[];self.links=[];self.href=None;self.anchor=[];self.h1=False;self.title=[];self.publication=None;self.meta_title=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('script','style'):self.skip+=1
        if tag=='h1':self.h1=True
        if tag=='a':self.href=a.get('href');self.anchor=[]
        if tag=='meta' and a.get('property')=='article:published_time':self.publication=a.get('content')
        if tag=='meta' and a.get('property')=='og:title':self.meta_title=a.get('content')
        if tag=='time' and a.get('datetime'):self.publication=self.publication or a['datetime']
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag=='h1':self.h1=False
        if tag=='a' and self.href:self.links.append((self.href,' '.join(self.anchor)));self.href=None
    def handle_data(self,data):
        if self.skip:return
        self.parts.append(data)
        if self.h1:self.title.append(data)
        if self.href:self.anchor.append(data)

def approved(url,hosts):
    p=urllib.parse.urlsplit(url)
    return p.scheme=='https' and p.hostname in hosts and not p.username and not p.password and p.port in (None,443) and not p.fragment

def get_page(url,hosts,page_factory=Page):
    if not approved(url,hosts):raise ValueError('unapproved IR destination')
    class Redirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            if not approved(newurl,hosts) or getattr(req,'hops',0)>=2:raise ValueError('IR redirect rejected')
            r=super().redirect_request(req,fp,code,msg,headers,newurl);r.hops=getattr(req,'hops',0)+1;return r
    opener=urllib.request.build_opener(Redirects())
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'PULSE/3 Public IR metadata (+https://github.com/roeeazaria55/pulse-investment-research./issues)','Accept':'text/html'})
            start=time.monotonic()
            with opener.open(req,timeout=12) as response:
                content=response.headers.get('Content-Type','')
                if 'html' not in content:raise ValueError('IR content is not HTML; no PDF parser enabled')
                chunks=[];size=0
                while True:
                    if time.monotonic()-start>25:raise TimeoutError('IR total timeout')
                    chunk=response.read(32768)
                    if not chunk:break
                    size+=len(chunk)
                    if size>1024*1024:raise ValueError('IR size limit')
                    chunks.append(chunk)
                body=b''.join(chunks).decode('utf-8',errors='replace')
                page=page_factory();page.feed(body)
                return page
        except urllib.error.HTTPError as exc:
            if exc.code in (401,403,451) or (exc.code!=429 and exc.code<500) or attempt:raise
        except (urllib.error.URLError,TimeoutError):
            if attempt:raise
        time.sleep(3)

MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
DATE=r'('+'|'.join(MONTHS)+r')\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})'

def parse_release(page,url,company,now):
    title=' '.join((' '.join(page.title) or page.meta_title or '').split())[:1000]
    text=' '.join(' '.join(page.parts).split())
    if not title or not any(a.casefold() in title.casefold() for a in [company['name'],*company['aliases']]):return None
    lower=title.lower()
    if not any(x in lower for x in ('quarter','fiscal year','financial results','דוח','תוצאות')):return None
    period_match=re.search(r'(first|second|third|fourth|[1-4](?:st|nd|rd|th))\s+(?:fiscal\s+)?quarter(?:\s+(?:fiscal\s+)?(?:year\s+)?)?(20\d{2})?',title,re.I)
    period=period_match.group(0) if period_match else title[:160]
    future=any(x in lower for x in ('to report','to announce','timing of','announces date','announce date','schedule'))
    actual=not future and ('reports' in lower or ('announces' in lower and 'results' in lower))
    if actual:
        # No guessed publication date: do not stamp collection time as publication.
        publication=page.publication if page.publication and re.match(r'^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$',page.publication) else None
        return {'kind':'results-published','period':period,'sourceUrl':url,'headline':title,'publishedAt':publication,
                'firstDetectedAt':now,'verifiedOfficial':True}
    if future:
        # Restrict extraction to the release heading plus sentences that explicitly
        # announce a release. A conference-call time is never a results time.
        candidates=re.findall(r'(?:will release|will announce|plans to announce|intends to release|financial results will be released)[^.]{0,500}',text,re.I)
        candidates=[s for s in candidates if re.search(r'(?:results|earnings)',s,re.I)]
        if re.search(r'to (?:report|announce).*results\s+on\b',title,re.I):candidates.append(title)
        on_date=r'\bon\s+(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+)?'+DATE
        match=next((m for s in candidates if (m:=re.search(on_date,s,re.I))),None)
        if not match:return None
        date=dt.date(int(match[3]),MONTHS[match[1].title()],int(match[2])).isoformat()
        if date<dt.datetime.fromisoformat(now).date().isoformat():return None
        kind='earnings-call' if 'will hold' in text.lower() and 'earnings conference call' in text.lower() and not any('results' in s.lower() for s in candidates[:-1]) else 'results-date'
        return {'kind':'date-announced','period':period,'date':date,'time':None,'timeZone':None,'sourceUrl':url,'headline':title,'eventKind':kind,'verifiedOfficial':True}
    return None

def collect_calendar(registry,previous,now,getter=get_page,pause=time.sleep):
    old={e['securityId']:e for e in previous.get('events',[])}
    events=[];sources=[];releases=list(previous.get('releases',[]))
    seen_urls={r['sourceUrl'] for r in releases}
    for company in registry['companies']:
        sid=company['securityId'];event=copy.deepcopy(old.get(sid) or dict(company['event'],securityId=sid,name=company['name']))
        status={'securityId':sid,'lastAttemptAt':now,'lastSuccessfulAt':next((s['lastSuccessfulAt'] for s in previous.get('sources',[]) if s['securityId']==sid),None),'status':'no-source','error':None,'url':company['indexUrl']}
        if company['indexUrl']:
            try:
                page=getter(company['indexUrl'],company['allowedHosts'])
                links=[]
                for href,title in page.links:
                    if re.search(r'(?:results|earnings|financial|דוח|תוצאות)',title,re.I):
                        target=urllib.parse.urljoin(company['indexUrl'],href).split('#')[0]
                        if approved(target,company['allowedHosts']) and target not in links and not target.lower().endswith('.pdf'):links.append(target)
                if event.get('sourceUrl') and approved(event['sourceUrl'],company['allowedHosts']):links.insert(0,event['sourceUrl'])
                parsed=[];release_errors=0
                for link in list(dict.fromkeys(links))[:3]:
                    pause(2)
                    try:
                        release=parse_release(getter(link,company['allowedHosts']),link,company,now)
                        if release:parsed.append(release)
                    except Exception:release_errors+=1
                status.update(status='partial' if release_errors else 'ok',lastSuccessfulAt=now,error='Some release pages unavailable' if release_errors else None)
                dates=sorted([r for r in parsed if r['kind']=='date-announced'],key=lambda r:r['date'])
                if dates:
                    found=dates[0]
                    if event.get('date')!=found['date']:
                        event.update(date=found['date'],time=None,timeZone=None,timing=None,call=None,period=found['period'],sourceUrl=found['sourceUrl'],status='confirmed',eventKind=found['eventKind'],verifiedAt=now[:10],verificationMethod='Parsed explicit future event date in official issuer release.',changedAt=now)
                    else:event['verifiedAt']=now[:10]
                for r in parsed:
                    if r['kind']=='results-published' and r['sourceUrl'] not in seen_urls:
                        r.update(securityId=sid,name=company['name'],id='results:'+hashlib.sha256((sid+r['sourceUrl']).encode()).hexdigest()[:24])
                        releases.append(r);seen_urls.add(r['sourceUrl'])
            except Exception as exc:status.update(status='failed',error=str(exc)[:200])
            pause(2)
        # Stable identity is company + normalized reporting period, independent of date revisions.
        raw=(event.get('period') or 'unknown').lower()
        quarter=next((str(i) for i,w in enumerate(['first','second','third','fourth'],1) if w in raw),None)
        if not quarter:
            m=re.search(r'q([1-4])',raw);quarter=m[1] if m else None
        year=re.search(r'20\d{2}',raw)
        stable_period=('q'+quarter+':'+year[0]) if quarter and year else raw
        event['id']='earnings:'+sid+':'+hashlib.sha256(stable_period.encode()).hexdigest()[:12]
        event['revision']=hashlib.sha256(json_key(event).encode()).hexdigest()[:16]
        events.append(event);sources.append(status)
    return {'events':events,'sources':sources,'releases':releases[-100:],'lastAttemptAt':now}

def json_key(event):return '|'.join(str(event.get(k) or '') for k in ('date','time','timeZone','eventKind','status'))
