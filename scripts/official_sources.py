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

# Persisted pulse-data is a cache, not an authenticated issuer or reviewer.
# Keep only the fields produced by this collector. Never carry unknown keys,
# e.g. forged approval flags or model instructions, into public snapshots.
PERSISTED_ITEM_FIELDS = frozenset((
    'id', 'companyId', 'ticker', 'title', 'sourceKind', 'issuerEvidenceUrl',
    'sourceLabel', 'url', 'indexRank', 'sourceId', 'kind', 'publishedDate',
    'collectedAt', 'lastSeenAt', 'metadataStatus', 'metadataCheckedAt',
    'metadataError', 'contentScope', 'publishedDateBasis', 'dateEvidenceUrl',
    'titleBasis', 'language', 'documentPeriod', 'periodBasis',
))

def _past_timestamp(value, now):
    try:
        timestamp=dt.datetime.fromisoformat(value)
        reference=dt.datetime.fromisoformat(now)
        return bool(timestamp.tzinfo and reference.tzinfo and timestamp<=reference)
    except (ValueError, TypeError, OverflowError):
        return False

def restore_previous(item, company, now):
    """Revalidate identity and sanitize cached metadata before any network call.

    If identity has been tampered with, stop the entire run BEFORE publishing a
    new snapshot. A failed refresh must never silently erase legitimate history.
    """
    if not isinstance(item,dict) or item.get('companyId')!=company['id']:
        return None
    url=item.get('url')
    if not isinstance(url,str) or not document_url(url,company):
        # Do not silently discard historical evidence on an HTTP 403 if a
        # persisted URL was forged or an issuer allowlist was tightened.
        raise ValueError('Persisted official item destination no longer allowlisted')
    expected='official:'+hashlib.sha256((company['id']+'|'+canonical(url)).encode()).hexdigest()[:32]
    sources={source['id']:source for source in company['sources']}
    if (item.get('id')!=expected or canonical(url)!=url or
        item.get('sourceId') not in sources or item.get('ticker')!=company['ticker']):
        raise ValueError('Persisted official item identity/source mismatch')
    if (not isinstance(item.get('title'),str) or
        not 1<=len(item['title'])<=600 or
        item.get('kind') not in ('release','results','schedule','document') or
        type(item.get('indexRank')) is not int or
        not 0<=item['indexRank']<=100 or
        item.get('titleBasis') not in (None,'page-heading','link-label','filename','index-context') or
        item.get('periodBasis') not in (None,'unknown','index-heading','filename-hint','title') or
        item.get('language') not in (None,'he','en') or
        not _past_timestamp(item.get('collectedAt'),now) or
        not _past_timestamp(item.get('lastSeenAt'),now)):
        raise ValueError('Persisted official item has invalid title or timestamps')
    clean_item={k:item[k] for k in PERSISTED_ITEM_FIELDS if k in item}
    source=sources[item['sourceId']]
    clean_item['sourceKind']=source.get('kind','company-ir')
    clean_item['issuerEvidenceUrl']=source['url'] if source.get('kind')=='issuer-distributed' else None
    clean_item['sourceLabel']=clean(item.get('sourceLabel') or item['title'])
    clean_item['contentScope']='metadata-only'
    clean_item['metadataError']=clean(str(item.get('metadataError') or ''))[:180] or None
    period=clean_item.get('documentPeriod')
    if period is not None and (not isinstance(period,str) or len(period)>160):
        clean_item.update(documentPeriod=None,periodBasis='unknown')
    if clean_item.get('metadataStatus') not in ('index-link','page-metadata'):
        clean_item.update(metadataStatus='index-link',metadataCheckedAt=None)
    # An impossible or untraceable cached date is not publication evidence.
    published=iso_date(clean_item.get('publishedDate'))
    evidence=clean_item.get('dateEvidenceUrl')
    basis=clean_item.get('publishedDateBasis')
    if (not published or published>now[:10] or
        evidence not in (url,source['url']) or
        basis not in ('index-time','page-published-metadata','unknown')):
        clean_item.update(publishedDate=None,publishedDateBasis='unknown',dateEvidenceUrl=None)
    else:
        clean_item['publishedDate']=published
    return clean_item

def get_official_page(url,hosts):return get_page(url,hosts,page_factory=OfficialPage)

def collect(config,previous,now,getter=get_official_page):
    old_items=previous.get('items',[])
    items={}
    for item in old_items:
        if not isinstance(item,dict):
            raise ValueError('Invalid persisted official item')
        company=next((c for c in config['companies'] if item.get('companyId')==c['id']),None)
        if company:
            fixed=restore_previous(item,company,now)
            if fixed is None:continue
            if fixed['id'] in items:
                raise ValueError('Duplicate persisted official item identity')
            retained={k:fixed[k] for k in ('title','titleBasis','language','documentPeriod','periodBasis') if k in fixed}
            described=describe(company,fixed['url'],fixed['title'])
            fixed={**fixed,**described}
            if retained.get('titleBasis'):
                fixed.update(retained)
            items[fixed['id']]=fixed
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
