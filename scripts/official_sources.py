"""Bounded issuer metadata collection. No document bodies or AI summaries published."""
import datetime as dt
import hashlib
import json
import re
import urllib.parse
from pathlib import Path
from earnings import get_page, approved

def date_only(value):
    if not isinstance(value,str):return None
    m=re.match(r'^(\d{4}-\d{2}-\d{2})(?:T.*)?$',value.strip())
    if not m:return None
    try:return dt.date.fromisoformat(m[1]).isoformat()
    except ValueError:return None

def kind(title,url):
    t=title.lower()
    if url.lower().split('?')[0].endswith('.pdf') or '/static-files/' in url or '/assets/' in url:return 'document'
    if any(x in t for x in ('to report','to release','date of','timing of')):return 'schedule'
    if re.search(r'\b(reports|reported)\b.*\bresults\b',t):return 'results'
    if any(x in t for x in ('presentation','slides','letter to shareholders','shareholder letter')):return 'document'
    return 'release'

def canonical(url):
    p=urllib.parse.urlsplit(url)
    # Keep query parameters: a signed/identified document may need them.
    return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,p.query,''))

def document_url(url,company):
    return (approved(url,company['allowedHosts']) and
            any(urllib.parse.urlsplit(url).path.startswith(p) for p in company['documentPaths']))

def collect(config,previous,now,getter=get_page):
    old_items=previous.get('items',[])
    items={i['id']:dict(i) for i in old_items if any(i['companyId']==c['id'] and document_url(i['url'],c) for c in config['companies'])}
    statuses=[]
    for company in config['companies']:
        detail_count=0
        for source in company['sources']:
            old=next((s for s in previous.get('sources',[]) if s['id']==source['id']),{})
            status={**source,'companyId':company['id'],'status':'failed','lastAttemptAt':now,
                    'lastSuccessfulAt':old.get('lastSuccessfulAt'),'count':0,'error':None}
            try:
                page=getter(source['url'],company['allowedHosts'])
                # get_page uses the shared HTML parser. Only allowlisted document
                # links are followed; scripts and response text are never executed.
                links={}
                for href,title in page.links:
                    url=canonical(urllib.parse.urljoin(source['url'],href))
                    if document_url(url,company) and 8<=len(title)<=600:
                        if url not in links or len(title)>len(links[url]):links[url]=title
                if not links:raise ValueError('No supported document links; page may require JavaScript or review')
                for rank,(url,title) in enumerate(list(links.items())[:8]):
                    ident='official:'+hashlib.sha256((company['id']+'|'+url).encode()).hexdigest()[:32]
                    old_item=items.get(ident,{})
                    record={**old_item,'id':ident,'companyId':company['id'],'ticker':company['ticker'],
                            'title':title,'url':url,'indexRank':rank,'sourceId':source['id'],'kind':kind(title,url),
                            'publishedDate':old_item.get('publishedDate'),'collectedAt':old_item.get('collectedAt',now),
                            'lastSeenAt':now,'metadataStatus':'index-link','metadataCheckedAt':old_item.get('metadataCheckedAt'),
                            'metadataError':None,'contentScope':'metadata-only'}
                    # Three release pages per company, no PDF fetching/parsing. A
                    # document link is not evidence that its contents were read.
                    if detail_count<3 and record['kind']!='document':
                        detail_count+=1
                        try:
                            detail=getter(url,company['allowedHosts'])
                            heading=' '.join(detail.title).strip() or detail.meta_title
                            if not heading or len(heading)>600:raise ValueError('Release heading unavailable')
                            record.update(title=heading,kind=kind(heading,url),
                                          publishedDate=date_only(detail.publication),metadataStatus='page-metadata',metadataCheckedAt=now)
                        except Exception as exc:record['metadataError']=str(exc)[:180]
                    items[ident]=record;status['count']+=1
                status.update(status='ok',lastSuccessfulAt=now)
            except Exception as exc:status['error']=str(exc)[:180]
            statuses.append(status)
    # Stable IDs retain first collection time; current visibility is separate.
    retained=sorted(items.values(),key=lambda i:(i['publishedDate'] or '',i['lastSeenAt'],-i.get('indexRank',0),i['id']),reverse=True)
    retained=[i for c in config['companies'] for i in [x for x in retained if x['companyId']==c['id']][:24]]
    return {'version':1,'generatedAt':now,'registry':config,'items':retained,'sources':statuses,
            'notice':'כותרות, קישורים ותאריכי פרסום כאשר זמינים. תוכן המסמכים לא נאסף ולא סוכם ב־AI.'}

if __name__=='__main__':
    path=Path('public/data/official-sources.json')
    previous=json.loads(path.read_text()) if path.exists() else {}
    config=json.loads(Path('public/data/official-registry.json').read_text())
    result=collect(config,previous,dt.datetime.now(dt.timezone.utc).isoformat())
    tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
    print(json.dumps({'items':len(result['items']),'sources':result['sources']}))
