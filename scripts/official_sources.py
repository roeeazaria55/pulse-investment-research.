"""Bounded issuer metadata collection. No document bodies or AI summaries published."""
import datetime as dt
import hashlib
import json
import re
import time
import urllib.parse
from pathlib import Path
from earnings import get_page, approved
from official_metadata import OfficialPage, describe, clean, iso_date, organization_key

def date_only(value):
    if not isinstance(value,str):return None
    m=re.match(r'^(\d{4}-\d{2}-\d{2})(?:T.*)?$',value.strip())
    if not m:return None
    try:return dt.date.fromisoformat(m[1]).isoformat()
    except ValueError:return None

def kind(title,url):
    t=title.lower()
    if 'maya.tase.co.il/he/reports/' in url or 'www.sec.gov/Archives/edgar/data/' in url:return 'document'
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
    return (not re.search(r'\.(?:png|jpe?g|gif|svg|webp|css|js|ico)$',urllib.parse.urlsplit(url).path,re.I) and approved(url,company['allowedHosts']) and
            any(urllib.parse.urlsplit(url).path.startswith(p) for p in company['documentPaths']))

def get_official_page(url,hosts):return get_page(url,hosts,page_factory=OfficialPage)

def collect(config,previous,now,getter=get_official_page):
    old_items=previous.get('items',[])
    items={}
    for item in old_items:
        company=next((c for c in config['companies'] if item['companyId']==c['id'] and document_url(item['url'],c)),None)
        if company:
            fixed={**item,**describe(company,item['url'],item['title'])}
            if item.get('titleBasis'):fixed.update({k:item[k] for k in ('title','titleBasis','language','documentPeriod','periodBasis') if k in item})
            fixed.setdefault('publishedDateBasis','legacy-metadata' if fixed.get('publishedDate') else 'unknown')
            fixed.setdefault('dateEvidenceUrl',fixed['url'] if fixed.get('publishedDate') else None)
            items[item['id']]=fixed
    statuses=[]
    deadline=time.monotonic()+240
    for company in config['companies']:
        detail_count=0
        for source in company['sources']:
            old=next((s for s in previous.get('sources',[]) if s['id']==source['id']),{})
            status={**source,'companyId':company['id'],'status':'failed','lastAttemptAt':now,
                    'lastSuccessfulAt':old.get('lastSuccessfulAt'),'count':0,'error':None}
            try:
                if time.monotonic()>deadline:raise ValueError('Collection time budget exhausted; retained items require later refresh')
                if source.get('format')=='sec-submissions':
                    from sec_metadata import submissions_page
                    page=submissions_page(source,company)
                else:page=getter(source['url'],company['allowedHosts'])
                # get_page uses the shared HTML parser. Only allowlisted document
                # links are followed; scripts and response text are never executed.
                links={}
                navigation_urls={canonical(urllib.parse.urljoin(source['url'],href)) for href,context in getattr(page,'link_contexts',{}).items() if context.get('navigationOnly')}
                content_urls={canonical(urllib.parse.urljoin(source['url'],href)) for href,context in getattr(page,'link_contexts',{}).items() if not context.get('navigationOnly')}
                navigation_urls-=content_urls
                # Remove previously misclassified menu documents only after a
                # successful read proves that the same URL is navigation-only.
                items={ident:item for ident,item in items.items() if not (item['companyId']==company['id'] and item.get('sourceId')==source['id'] and item['url'] in navigation_urls)}
                for href,title in page.links:
                    url=canonical(urllib.parse.urljoin(source['url'],href))
                    context=getattr(page,'link_contexts',{}).get(href,{})
                    verified_publisher=source.get('kind')!='issuer-distributed' or context.get('publisherKey')==organization_key(source['url'])
                    if url not in navigation_urls and verified_publisher and document_url(url,company) and 1<=len(clean(title))<=600:
                        if url not in links or len(title)>len(links[url]):links[url]=title
                if not links:raise ValueError('No supported document links; page may require JavaScript or review')
                for rank,(url,title) in enumerate(list(links.items())[:8]):
                    ident='official:'+hashlib.sha256((company['id']+'|'+url).encode()).hexdigest()[:32]
                    old_item=items.get(ident,{})
                    context=getattr(page,'link_contexts',{}).get(next((href for href,_ in page.links if canonical(urllib.parse.urljoin(source['url'],href))==url),url),{})
                    # Index dates apply only to release cards, not financial PDF
                    # periods or dates embedded in document paths/filenames.
                    index_date=context.get('publishedDate') if kind(title,url)!='document' or source.get('publicationDates') is True else None
                    if index_date and index_date>now[:10]:index_date=None
                    record={**old_item,'id':ident,'companyId':company['id'],'ticker':company['ticker'],
                            'title':title,'sourceKind':source.get('kind','company-ir'),'issuerEvidenceUrl':source['url'] if source.get('kind')=='issuer-distributed' else None,'sourceLabel':clean(title),'url':url,'indexRank':rank,'sourceId':source['id'],'kind':kind(title,url),
                            'publishedDate':old_item.get('publishedDate'),'collectedAt':old_item.get('collectedAt',now),
                            'lastSeenAt':now,'metadataStatus':'index-link','metadataCheckedAt':old_item.get('metadataCheckedAt'),
                            'metadataError':None,'contentScope':'metadata-only',
                            'publishedDateBasis':old_item.get('publishedDateBasis','unknown'),
                            'dateEvidenceUrl':old_item.get('dateEvidenceUrl')}
                    record.update(describe(company,url,title,context))
                    if index_date:record.update(publishedDate=index_date,publishedDateBasis='index-time',dateEvidenceUrl=source['url'])
                    # Three release pages per company, no PDF fetching/parsing. A
                    # document link is not evidence that its contents were read.
                    if source.get('format')!='sec-submissions' and detail_count<(3 if company['ticker'] in ('NBIS','IREN','DLO') else 1) and record['kind']!='document' and time.monotonic()<deadline:
                        detail_count+=1
                        try:
                            detail=getter(url,company['allowedHosts'])
                            heading=clean(' '.join(detail.title)) or clean(detail.meta_title)
                            if not heading or len(heading)>600:raise ValueError('Release heading unavailable')
                            record.update(describe(company,url,title,context,page_title=heading))
                            record.update(kind=kind(heading,url),metadataStatus='page-metadata',metadataCheckedAt=now)
                            publication=iso_date(detail.publication_value if isinstance(detail,OfficialPage) else detail.publication)
                            if publication and publication<=now[:10]:record.update(publishedDate=publication,publishedDateBasis='page-published-metadata',dateEvidenceUrl=url)
                        except Exception as exc:record['metadataError']=str(exc)[:180]
                    items[ident]=record;status['count']+=1
                status.update(status='ok',lastSuccessfulAt=now)
            except Exception as exc:status['error']=str(exc)[:180]
            statuses.append(status)
    # Stable IDs retain first collection time; current visibility is separate.
    retained=sorted(items.values(),key=lambda i:(i['publishedDate'] or '',i['lastSeenAt'],-i.get('indexRank',0),i['id']),reverse=True)
    retained=[i for c in config['companies'] for i in [x for x in retained if x['companyId']==c['id']][:24]]
    return {'version':1,'metadataVersion':2,'generatedAt':now,'registry':config,'items':retained,'sources':statuses,
            'notice':'כותרות, קישורים ותאריכי פרסום כאשר זמינים. תוכן המסמכים לא נאסף ולא סוכם ב־AI.'}

if __name__=='__main__':
    path=Path('public/data/official-sources.json')
    previous=json.loads(path.read_text()) if path.exists() else {}
    config=json.loads(Path('public/data/official-registry.json').read_text())
    result=collect(config,previous,dt.datetime.now(dt.timezone.utc).isoformat())
    tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
    print(json.dumps({'items':len(result['items']),'sources':result['sources']}))
