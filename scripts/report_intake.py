"""Bounded official report content intake. No AI, inferred targets or automatic thesis edits."""
import datetime as dt
import hashlib
import io
import json
import math
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from official_sources import document_url, canonical

VERSION=1
PARSER='official-content-v1'
MAX_BYTES=8*1024*1024
PILOTS={c["id"] for c in json.loads((Path(__file__).resolve().parent.parent/"public/data/official-registry.json").read_text(encoding="utf-8"))["companies"]}
LABELS=re.compile(r'revenue|net (?:income|loss)|gross profit|operating (?:income|loss)|cash flow|inventor|accounts receivable|total assets|earnings per|TPV|remaining performance|הכנסות|רווח|מלאי|תזרים',re.I)
FISCAL_YEAR=re.compile(r'\bFY\s*((?:20)?\d{2})\b',re.I)
FINANCIAL_TITLE=re.compile(r'financial|fiscal|quarter|\bQ[1-4]\b|\bFY\s*(?:20)?\d{2}\b|annual report|10-K|10-Q|20-F|shareholder|תוצאות כספיות|דוח כספי|דוחות כספיים|דוח רבעון',re.I)
SCHEDULE=re.compile(r'to (?:report|release|announce)|date (?:of|for)|timing of|schedule|earnings call registration',re.I)
KNOWN_FACTS={'us-gaap:revenues','us-gaap:revenuefromcontractwithcustomerexcludingassessedtax','us-gaap:netincomeloss','us-gaap:grossprofit','us-gaap:operatingincomeloss','us-gaap:netcashprovidedbyusedinoperatingactivities','us-gaap:inventorynet','us-gaap:accountsreceivablenetcurrent','us-gaap:cashandcashequivalentsatcarryingvalue','us-gaap:weightedaveragenumberofdilutedsharesoutstanding','us-gaap:earningspersharediluted'}
def clean(value):return ' '.join(value.split())
def valid_day(value):
 try:return dt.date.fromisoformat(value).isoformat()==value
 except (TypeError,ValueError):return False

def safe_report_url(url,company):
 try:
  path=urllib.parse.unquote(urllib.parse.urlsplit(url).path)
  return document_url(url,company) and not any(part in ('.','..') for part in path.split('/'))
 except (ValueError,TypeError):return False

def ascii_report_url(url,company):
 """Percent-encode non-ASCII path chars on already-allowlisted issuer URLs.
 This is ordinary URL encoding, not an authentication or access bypass.
 """
 if not safe_report_url(url,company):raise ValueError('Report URL outside issuer allowlist')
 p=urllib.parse.urlsplit(url)
 encoded=urllib.parse.urlunsplit((p.scheme,p.netloc,
          urllib.parse.quote(p.path,safe='/%-._~'),
          urllib.parse.quote(p.query,safe='=&/%?+-._~'),'')) 
 if not safe_report_url(encoded,company):raise ValueError('Encoded report URL escaped issuer allowlist')
 return encoded

def fetch_document(url,company):
 url=ascii_report_url(url,company)
 class Redirects(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,req,fp,code,msg,headers,newurl):
   if not safe_report_url(newurl,company) or getattr(req,'hops',0)>=2:raise ValueError('Report redirect outside issuer allowlist')
   nxt=super().redirect_request(req,fp,code,msg,headers,newurl);nxt.hops=getattr(req,'hops',0)+1;return nxt
 req=urllib.request.Request(url,headers={'User-Agent':'PULSE public research (+https://github.com/roeeazaria55/pulse-investment-research./issues)','Accept':'text/html,application/pdf,application/xhtml+xml'})
 start=time.monotonic()
 with urllib.request.build_opener(Redirects()).open(req,timeout=12) as response:
  final=response.geturl()
  if not safe_report_url(final,company):raise ValueError('Unapproved final destination')
  chunks=[];size=0
  while True:
   if time.monotonic()-start>25:raise TimeoutError('Report total timeout')
   chunk=response.read(32768)
   if not chunk:break
   size+=len(chunk)
   if size>MAX_BYTES:raise ValueError('Report exceeds 8MB')
   chunks.append(chunk)
  return b''.join(chunks),response.headers.get('Content-Type','').split(';')[0].lower(),final

class ReportHTML(HTMLParser):
 def __init__(self):
  super().__init__();self.skip=0;self.parts=[];self.heading=[];self.in_heading=False;self.title=[];self.in_title=False;self.meta_title='';self.tables=[];self.stack=[];self.context=None;self.contexts={};self.context_field=None;self.fact=None;self.facts=[];self.unit=None;self.units={};self.unit_parts=[];self.link=None;self.links=[];self.link_parts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);local=tag.split(':')[-1]
  if tag in ('script','style','noscript'):self.skip+=1
  if tag=='meta' and a.get('property') in ('og:title','twitter:title'):self.meta_title=a.get('content','')
  if tag=='h1':self.in_heading=True
  if tag=='title':self.in_title=True
  if tag=='a':self.link=a.get('href');self.link_parts=[]
  if local=='context':self.context={'id':a.get('id'),'dimensioned':False};self.context_field=None
  if self.context is not None:
   if local in ('startdate','enddate','instant','identifier'):self.context_field=local;self.context[local]=''
   if local in ('explicitmember','typedmember','segment','scenario'):self.context['dimensioned']=True
  if local=='unit':self.unit=a.get('id');self.unit_parts=[]
  if tag=='ix:nonfraction':self.fact={'name':a.get('name','').lower(),'context':a.get('contextref'),'unit':a.get('unitref'),'scale':a.get('scale','0'),'sign':a.get('sign',''),'text':[],'format':a.get('format','')}
  if tag=='table':self.stack.append({'rows':[],'row':None,'cell':None,'spans':False})
  if self.stack:
   table=self.stack[-1]
   if tag=='tr':table['row']=[]
   if tag in ('td','th'):
    table['cell']=[]
    if a.get('colspan','1')!='1' or a.get('rowspan','1')!='1':table['spans']=True
 def handle_data(self,data):
  if self.skip:return
  self.parts.append(data)
  if self.in_heading:self.heading.append(data)
  if self.in_title:self.title.append(data)
  if self.link:self.link_parts.append(data)
  if self.context is not None and self.context_field:self.context[self.context_field]+=data
  if self.unit:self.unit_parts.append(data)
  if self.fact is not None:self.fact['text'].append(data)
  if self.stack and self.stack[-1]['cell'] is not None:self.stack[-1]['cell'].append(data)
 def handle_endtag(self,tag):
  local=tag.split(':')[-1]
  if tag in ('script','style','noscript'):self.skip=max(0,self.skip-1)
  if tag=='h1':self.in_heading=False
  if tag=='title':self.in_title=False
  if tag=='a' and self.link:self.links.append((self.link,clean(' '.join(self.link_parts))));self.link=None
  if local=='context' and self.context is not None:
   if self.context['id']:self.contexts[self.context['id']]=self.context
   self.context=None;self.context_field=None
  elif local==self.context_field:self.context_field=None
  if local=='unit' and self.unit:self.units[self.unit]=clean(' '.join(self.unit_parts));self.unit=None
  if tag=='ix:nonfraction' and self.fact is not None:self.facts.append(self.fact);self.fact=None
  if self.stack:
   table=self.stack[-1]
   if tag in ('td','th') and table['cell'] is not None:
    if table['row'] is not None:table['row'].append(clean(' '.join(table['cell'])))
    table['cell']=None
   if tag=='tr' and table['row'] is not None:
    if any(table['row']):table['rows'].append(table['row'])
    table['row']=None
   if tag=='table':
    if table['rows']:self.tables.append(table)
    self.stack.pop()

def issuer_ciks(company):
 return set(re.findall(r'/Archives/edgar/data/(\d+)/',' '.join(company['documentPaths'])))|{s['cik'] for s in company['sources'] if s.get('cik')}

def inline_facts(page,company):
 out=[];ciks=issuer_ciks(company)
 for f in page.facts:
  c=page.contexts.get(f['context'],{});unit=page.units.get(f['unit'],'')
  if f['name'] not in KNOWN_FACTS or c.get('dimensioned') or not ciks or c.get('identifier','').strip().lstrip('0') not in ciks:continue
  start=c.get('startdate');end=c.get('enddate') or c.get('instant')
  if not valid_day(end) or start is not None and not valid_day(start):continue
  # Only conventional dot-decimal inline numbers; transformed/locale-specific formats require review.
  if f['format'] and not f['format'].lower().endswith(('num-dot-decimal','numdotdecimal','num-dot-decimal-in')):continue
  text=clean(''.join(f['text']))
  if not re.fullmatch(r'\(?[\d,]+(?:\.\d+)?\)?',text):continue
  try:
   scale=int(f['scale'])
   if not -12<=scale<=12:continue
   value=float(text.replace(',','').strip('()'))*10**scale
   if f['sign']=='-' or text.startswith('('):value=-value
   if not math.isfinite(value):continue
  except (ValueError,OverflowError):continue
  if not unit or len(unit)>160:continue
  row=dict(concept=f['name'],value=value,unit=unit,start=start,end=end,context=f['context'],status='structured-source',definition='XBRL tag; not automatically equivalent to an analyst metric')
  if row not in out:out.append(row)
 return out[:150]

def extract(body,content_type,url,company):
 if len(body)>MAX_BYTES:raise ValueError('Report exceeds 8MB')
 pdf=body.startswith(b'%PDF');tables=[];facts=[];links=[];page_count=None;truncated=False
 if pdf:
  import pdfplumber
  with pdfplumber.open(io.BytesIO(body)) as doc:
   page_count=len(doc.pages);parts=[];parse_start=time.monotonic()
   for page in doc.pages[:60]:
    if time.monotonic()-parse_start>20:truncated=True;break
    parts.append(page.extract_text() or '')
    for table in (page.extract_tables() or page.extract_tables({'vertical_strategy':'text','horizontal_strategy':'text'})):
     rows=[[clean(str(cell or ''))[:250] for cell in row[:16]] for row in table]
     if any(LABELS.search(' '.join(row)) for row in rows):tables.append(dict(rows=rows[:35],spans=False,scope='PDF table; column order and units require review',page=page.page_number))
   text='\n'.join(parts);truncated=truncated or page_count>60
  title=clean(text[:600])[:300]
 else:
  if content_type not in ('text/html','application/xhtml+xml','text/plain'):raise ValueError('Unsupported report media type')
  page=ReportHTML();page.feed(body.decode('utf-8',errors='replace'))
  title=clean(page.meta_title or ' '.join(page.heading) or ' '.join(page.title))[:600];text=clean(' '.join(page.parts));facts=inline_facts(page,company);links=page.links
  for table in page.tables:
   if any(LABELS.search(' '.join(row)) for row in table['rows']):
    rows=table['rows'];selected=list(range(min(6,len(rows))))+[i for i,row in enumerate(rows) if LABELS.search(' '.join(row))]
    rows=[rows[i] for i in sorted(set(selected))[:35]]
    tables.append(dict(rows=[[cell[:250] for cell in row[:16]] for row in rows],spans=table['spans'],scope='Selected source rows; header periods and units require review',page=None))
 if not text.strip() or len(text.strip())<100:raise ValueError('No readable report body; OCR or dynamic rendering may be needed')
 if re.search(r'PULSE\s*(?:\||/)|מחקר השקעה|מחקר מקיף עבור',title,re.I):raise ValueError('User research is not an official company report')
 aliases=[company['name'],company['label'],*company.get('aliases',[])]
 if not any(a and a.casefold() in text[:30000].casefold() for a in aliases) and not facts:raise ValueError('Issuer identity absent from report body')
 if SCHEDULE.search(title) and not facts:raise ValueError('Schedule announcement is not a results report')
 if not tables and not facts and not FINANCIAL_TITLE.search(title):raise ValueError('Not a financial results document')
 if not tables and not facts:status='read-no-supported-data'
 else:status='extracted'
 # Do not guess fiscal periods or units from filenames, publication dates or collection dates.
 return dict(status=status,title=title or company['name'],sha256=hashlib.sha256(body).hexdigest(),bytes=len(body),format='pdf' if pdf else 'html',pages=page_count,readScope='partial-pages' if truncated else 'full-body',charactersRead=len(text),tables=tables[:12],tableCount=len(tables),tablesTruncated=len(tables)>12,facts=facts,reviewStatus='pending-review',links=links,notice='Content was read automatically. Table rows require period/unit review. No thesis or price target was updated.')

def candidates(snapshot,company):
 items=[i for i in snapshot.get('items',[]) if i['companyId']==company['id'] and i.get('kind') in ('results','document') and not SCHEDULE.search(i['title']) and FINANCIAL_TITLE.search(i['title']+' '+(i.get('documentPeriod') or '')) and safe_report_url(i['url'],company)]
 # Curated official pointers are *candidates* only; not documents, not
 # timestamps of a successful fetch and not analyst-approved numbers.
 # They are intentionally bound to issuer allowlisted domains before use.
 for r in company.get('curatedReportCandidates',[]):
  if not isinstance(r,dict) or not safe_report_url(r.get('url'),company) or not FINANCIAL_TITLE.search(str(r.get('title',''))+' '+str(r.get('documentPeriod') or '')):
   raise ValueError('Invalid curated issuer document URL/title')
  if r.get('publishedDate') is not None and not valid_day(r['publishedDate']):
   raise ValueError('Curated source publication date invalid')
  if not isinstance(r.get('evidence'),str) or not r['evidence'].startswith('https://'):
   raise ValueError('Curated source must cite verified issuer index')
  if not any(i['url']==r['url'] for i in items):
   items.append({'id':'curated:'+hashlib.sha256((company['id']+'|'+r['url']).encode()).hexdigest()[:32],
                 'companyId':company['id'],'url':r['url'],'title':r['title'],
                 'kind':'document','documentPeriod':r.get('documentPeriod'),
                 'periodBasis':'curated-issuer-title-unverified',
                 'publishedDate':r['publishedDate'],'publishedDateBasis':'curated-reference-only',
                 'sourceId':'curated-official-pointer','evidenceUrl':r['evidence']})
 def rank(item):
  period=item.get('documentPeriod') or item['title'];year=re.search(r'20\d{2}',period);fiscal=FISCAL_YEAR.search(period);quarter=re.search(r'Q([1-4])',period,re.I);word=re.search(r'(first|second|third|fourth)\s+(?:fiscal\s+)?quarter',period,re.I)
  q=int(quarter[1]) if quarter else {'first':1,'second':2,'third':3,'fourth':4}.get(word[1].lower(),0) if word else 0
  # FY26 is an issuer-supplied fiscal label used ONLY for discovery ranking.
  # It does not establish accounting start/end dates for extracted observations.
  y=2000+int(fiscal[1][-2:]) if fiscal else int(year[0]) if year else 0
  return (y,4 if fiscal and not q else q,item.get('publishedDate') or '',item.get('lastSeenAt') or '')
 return sorted(items,key=rank,reverse=True)

def collect(snapshot,registry,previous,now,fetcher=fetch_document,limit=16,budget=180):
 records={r['id']:r for r in previous.get('documents',[])};statuses=[];attempts=0;deadline=time.monotonic()+budget
 # Oldest actual content-fetch attempt goes first, preventing fixed registry
 # order from starving companies when the network request budget is exhausted.
 previous_status={s['companyId']:s for s in previous.get('sources',[]) if isinstance(s,dict) and isinstance(s.get('companyId'),str)}
 # Fill true missing-document gaps before re-checking already retained reports.
 # Within equal coverage tiers, rotate oldest attempt first to avoid starvation.
 have_doc={d.get('companyId') for d in previous.get('documents',[]) if
           isinstance(d,dict) and d.get('status')=='extracted'}
 ordered=sorted((c for c in registry['companies'] if c['id'] in PILOTS),
                key=lambda c: (c['id'] in have_doc,
                               previous_status.get(c['id'],{}).get('lastAttemptAt') or '',c['id']))
 for company in ordered:
  todo=candidates(snapshot,company)[:6]
  def priority(item):
   ident='report:'+hashlib.sha256((company['id']+'|'+canonical(item['url'])).encode()).hexdigest()[:32]
   return (ident in records,records.get(ident,{}).get('lastSuccessfulAt',''))
  todo.sort(key=priority);chosen=todo[:2];status=dict(companyId=company['id'],
     lastAttemptAt=previous_status.get(company['id'],{}).get('lastAttemptAt'),
     status='no-candidates',error=None)
  discovery=[s for s in snapshot.get('sources',[]) if s.get('companyId')==company['id']]
  if not chosen and discovery and all(s.get('status')=='failed' for s in discovery):
   detail=next((s.get('error') for s in discovery if s.get('error')),'Unknown discovery failure')
   status.update(status='failed',error=('Official source discovery failed; publication status unknown: '+detail)[:180])
  for item in chosen:
   if attempts>=limit or time.monotonic()>deadline:status.update(status='deferred',error='Run budget reached; retained records unchanged');break
   status['lastAttemptAt']=now
   url=canonical(item['url']);ident='report:'+hashlib.sha256((company['id']+'|'+url).encode()).hexdigest()[:32]
   prior=records.get(ident)
   # Recheck even stable URLs: issuers may replace a document without changing its URL.
   attempts+=1
   try:
    body,ctype,final=fetcher(url,company);result=extract(body,ctype,url,company)
    if result['format']=='html' and not result['tables'] and not result['facts']:
     attachments=[canonical(urllib.parse.urljoin(final,href)) for href,label in result.get('links',[]) if urllib.parse.urlsplit(urllib.parse.urljoin(final,href)).path.lower().endswith('.pdf') and safe_report_url(canonical(urllib.parse.urljoin(final,href)),company)]
     if attachments and attempts<limit and time.monotonic()<deadline:
      attempts+=1
      body,ctype,final=fetcher(attachments[0],company);result=extract(body,ctype,final,company)
    result.pop('links',None)
    changed=bool(prior and prior['sha256']!=result['sha256'])
    revisions=prior.get('revisions',[]) if prior else []
    if changed:revisions=([dict(sha256=prior['sha256'],firstDetectedAt=prior['firstDetectedAt'],lastSuccessfulAt=prior['lastSuccessfulAt'])]+revisions)[:3]
    record=dict(**result,id=ident,companyId=company['id'],ticker=company['label'],url=url,finalUrl=final,publishedDate=item.get('publishedDate'),documentPeriod=item.get('documentPeriod'),periodBasis=item.get('periodBasis','unknown'),firstDetectedAt=prior['firstDetectedAt'] if prior else now,lastSuccessfulAt=now,lastAttemptAt=now,revised=changed or bool(prior and prior.get('revised')),revisions=revisions,parserVersion=PARSER,error=None)
    records[ident]=record;status.update(status='partial' if status['status'] in ('failed','partial') or result['status'] != 'extracted' else 'ok',error=status['error'])
    if result['status'] == 'extracted':break
   except Exception as exc:
    status.update(status='partial' if status['status'] in ('ok','partial') else 'failed',error=str(exc)[:180])
    if prior:records[ident]={**prior,'lastAttemptAt':now,'error':str(exc)[:180]}
  statuses.append(status)
 docs=sorted(records.values(),key=lambda r:(r['lastSuccessfulAt'],r['id']),reverse=True)
 docs=[r for c in registry['companies'] for r in [x for x in docs if x['companyId']==c['id']][:6]]
 return dict(version=VERSION,generatedAt=now,parserVersion=PARSER,documents=docs,sources=statuses,notice='Official content intake pilot. Extracted facts and tables have not been applied to the research or valuation. Failure is not evidence that no report exists.')

def main():
 path=Path('public/data/report-intake.json');previous=json.loads(path.read_text()) if path.exists() else {}
 snapshot=json.loads(Path('public/data/official-sources.json').read_text());registry=json.loads(Path('public/data/official-registry.json').read_text())
 result=collect(snapshot,registry,previous,dt.datetime.now(dt.timezone.utc).isoformat())
 tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
 evidence=[{k:d[k] for k in ('companyId','url','finalUrl','sha256','lastSuccessfulAt','status','tableCount','error')}|{'structuredFacts':len(d['facts'])} for d in result['documents']]
 print(json.dumps({'documents':len(result['documents']),'sources':result['sources'],'documentEvidence':evidence}))
if __name__=='__main__':main()

