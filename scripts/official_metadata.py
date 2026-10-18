"""Conservative issuer-index metadata. No dates inferred from download paths."""
import datetime as dt
import json
import re
import urllib.parse
from earnings import Page

MONTHS={m.lower():i for i,m in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1)}
MONTHS.update({m[:3]:v for m,v in list(MONTHS.items())})

def clean(value):return ' '.join(str(value or '').split()).strip(' ›»→↗')[:600]
def iso_date(value):
    if not isinstance(value,str):return None
    m=re.fullmatch(r'(\d{4}-\d{2}-\d{2})(?:T.*)?',value.strip())
    if not m:return None
    try:return dt.date.fromisoformat(m[1]).isoformat()
    except ValueError:return None

def visible_date(value):
    value=clean(value)
    direct=iso_date(value)
    if direct:return direct
    patterns=(r'([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(20\d{2})',r'(\d{1,2})\s+([A-Za-z]+)\.?\s+(20\d{2})')
    for index,pattern in enumerate(patterns):
        m=re.fullmatch(pattern,value)
        if m:
            month=m[1 if index==0 else 2].lower();day=m[2 if index==0 else 1]
            if month not in MONTHS:return None
            try:return dt.date(int(m[3]),MONTHS[month],int(day)).isoformat()
            except ValueError:return None
    return None

GENERIC=re.compile(r'^(?:(?:eng|heb|en|he|pdf|download|view file|view|read more|להורדה|הורדה|עברית|אנגלית|קובץ|›|»|\W)+)$',re.I)
def useful(value):
    value=clean(value)
    return bool(len(value)>=8 and value.casefold() not in ('financials','financial information','news','press releases','investor relations','reports','מצגות','דוחות') and not GENERIC.fullmatch(value))

def language(label,url):
    text=clean(label)
    filename=urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/',1)[-1])
    if re.search(r'\b(?:HEB|עברית)\b',text,re.I):return 'he'
    if re.search(r'\b(?:ENG|אנגלית)\b',text,re.I):return 'en'
    if re.search(r'(?:^|[_\-])(?:He|HEB)(?:[_\-.]|\d)',filename):return 'he'
    if re.search(r'(?:^|[_\-])(?:En|ENG)(?:[_\-.]|\d)',filename):return 'en'
    return None

def period_hint(value):
    value=clean(value)
    q=re.search(r'\b(Q[1-4])\s*[-_ ]*(?:FY\s*)?(20\d{2})\b',value,re.I)
    if q:return q[1].upper()+' '+q[2]
    fy=re.search(r'\b(?:FY|full.year|annual report|periodic report)\s*[-_ ]*(20\d{2})\b',value,re.I)
    if fy:return 'FY '+fy[1]
    month=re.fullmatch(r'('+'|'.join(MONTHS)+r')\s+(20\d{2})(?:\s+investor presentation)?',value,re.I)
    if month:return month[1].title()+' '+month[2]
    return None

def describe(company,url,label,context=None,page_title=None):
    context=context or {}
    raw=clean(label); heading=clean(context.get('heading'))
    filename=urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/',1)[-1])
    stem=re.sub(r'\.(pdf|html?|aspx)$','',filename,flags=re.I)
    readable=clean(re.sub(r'[_\-]+',' ',stem))[:180]
    if useful(page_title):title,basis=clean(page_title),'page-heading'
    elif raw.casefold() in ('earnings release','letter to shareholders','press release') and useful(heading):title,basis=heading+' — '+raw,'index-context'
    elif useful(raw):title,basis=raw,'link-label'
    elif useful(heading):title,basis=heading,'index-context'
    else:title,basis=company['name']+' — '+(readable or 'מסמך רשמי'),'filename'
    lang=language(raw,url)
    period=period_hint(heading) or period_hint(title)
    period_basis='index-heading' if period_hint(heading) else ('filename-hint' if basis=='filename' else 'title') if period else 'unknown'
    if not period:
        period=period_hint(readable);period_basis='filename-hint' if period else 'unknown'
    if basis=='index-context' and lang:title+=' · '+('עברית' if lang=='he' else 'אנגלית')
    return {'title':title[:600],'titleBasis':basis,'language':lang,'documentPeriod':period,'periodBasis':period_basis}

class OfficialPage(Page):
    """Attach headings/dates only to small containing blocks, not page-wide text."""
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self):
        super().__init__();self.stack=[];self.link_contexts={};self.publication_value=None;self.publication_basis=None;self.jsonld=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);super().handle_starttag(tag,list(attrs.items()))
        prop=attrs.get('property') or attrs.get('name') or attrs.get('itemprop')
        if prop in ('article:published_time','datePublished') and iso_date(attrs.get('content')):
            self.publication_value=attrs['content'];self.publication_basis='page-published-metadata'
        if tag=='script' and attrs.get('type')=='application/ld+json':self.jsonld=''
        if tag not in self.VOID and len(self.stack)<128:
            self.stack.append({'tag':tag,'attrs':attrs,'text':[],'headings':[],'dates':[],'links':[]})
    def handle_data(self,data):
        super().handle_data(data)
        if self.jsonld is not None:
            if len(self.jsonld)<100000:self.jsonld+=data
            return
        if self.skip:return
        for node in self.stack:
            if sum(map(len,node['text']))<3000:node['text'].append(data)
    def handle_endtag(self,tag):
        super().handle_endtag(tag)
        if tag=='script' and self.jsonld is not None:
            try:
                root=json.loads(self.jsonld)
                candidates=root if isinstance(root,list) else [root]
                for obj in candidates:
                    if isinstance(obj,dict) and isinstance(obj.get('@graph'),list):candidates.extend(obj['@graph'][:30])
                for obj in candidates[:50]:
                    if isinstance(obj,dict) and obj.get('@type') in ('Article','NewsArticle','Report') and iso_date(obj.get('datePublished')):
                        self.publication_value=self.publication_value or obj['datePublished'];self.publication_basis='page-published-metadata'
            except (ValueError,TypeError):pass
            self.jsonld=None
        match=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i]['tag']==tag),None)
        if match is None:return
        nodes=self.stack[match:];self.stack=self.stack[:match]
        node=nodes[0];text=clean(' '.join(node['text']));attrs=node['attrs']
        if tag in ('h1','h2','h3','h4','h5','h6') and useful(text):
            for ancestor in self.stack:
                if len(ancestor['headings'])<6:ancestor['headings'].append(text)
        explicit_date=tag=='time' or bool(re.search(r'(?:publish|news.*date|date.*news|release.*date|date.*release|(?:^|[\s_-])date(?:$|[\s_-]))',attrs.get('class',''),re.I))
        date=iso_date(attrs.get('datetime')) or visible_date(text) if explicit_date else None
        if date:
            for ancestor in self.stack:
                if len(ancestor['dates'])<4:ancestor['dates'].append(date)
        if tag=='a' and attrs.get('href'):
            href=attrs['href']
            for ancestor in self.stack:
                if len(ancestor['links'])<20:ancestor['links'].append(href)
            if node['dates']:self.link_contexts.setdefault(href,{}).setdefault('publishedDate',node['dates'][0])
        # A nearby card/section may link English and Hebrew versions of the same
        # document. Large page/nav containers cannot lend dates to every link.
        urls=set(node['links'])
        if 0<len(urls)<=4 and len(text)<3000:
            for href in urls:
                context=self.link_contexts.setdefault(href,{})
                if node['headings']:context.setdefault('heading',node['headings'][-1])
                if len(urls)==1 and len(set(node['dates']))==1:context.setdefault('publishedDate',node['dates'][0])
