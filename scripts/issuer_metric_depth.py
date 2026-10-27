"""Additional measures from exact, reviewed issuer statement layouts.

The base adapter must first validate issuer, report and period headers. Every
additional row independently requires a unique match; no inferred numbers.
"""
import re
from issuer_table_adapters import _proposal

TOKEN = r'(?:\([\d,]+(?:\.\d+)?\)|-?[\d,]+(?:\.\d+)?)'

def number(raw):
    raw=raw.strip().removeprefix('$').strip()
    if not re.fullmatch(TOKEN,raw): return None
    return float(raw.strip('()').replace(',',''))*(-1 if raw.startswith('(') else 1)


def enrich(doc, base):
    if not base: return base
    output=list(base)
    def add(key,label,a,b,row,page=None,scale=1,definition=None,instant=None):
        av,bv=number(a),number(b)
        if av is None or bv is None or any(m['id']==key for m in output):return
        ref=base[0]
        dates=(ref['periodStart'],ref['periodEnd'],ref['previousPeriodStart'],ref['previousPeriodEnd'])
        if instant: dates=(instant[0],instant[0],instant[1],instant[1])
        m=_proposal(doc,key,label,round(av/scale,6),round(bv/scale,6),a,b,*dates,
            ref['unit'],definition or ref['accountingBasis'],row,page,ref['evidenceScope'])
        if m:output.append(m)
    cid=doc['companyId']
    if cid=='candidate-nebius':
        pages={p['page']:p['text'] for p in doc.get('sourcePdfPages',[])}
        for page,key,label,source in [
            (7,'operatingIncome','הפסד תפעולי','Loss from operations'),
            (7,'netIncome','רווח/הפסד נקי כולל פעילות שהופסקה','Net income / (loss)'),
            (8,'operatingCash','תזרים תפעולי כולל פעילות שהופסקה','Net cash provided by / (used in) operating activities'),
            (8,'capex','רכוש וציוד ונכסים בלתי מוחשיים במזומן','Purchases of property and equipment and intangible assets')]:
            text=pages.get(page,'')
            if not ('Nebius Group N.V.' in text and 'millions of U.S. dollars' in text and
                'Three months ended June 30, Six months ended June 30,\n2025 2026 2025 2026' in text):continue
            matches=re.findall(r'^'+re.escape(source)+r' ('+TOKEN+r') ('+TOKEN+r') ('+TOKEN+r') ('+TOKEN+r')$',text,re.M)
            if len(matches)==1:
                prior,current,_,_=matches[0]
                add(key,label,current,prior,source,page,definition='US GAAP original consolidated Q2 statement; '+source+'; USD millions')
                if key=='capex':
                    m=next((m for m in output if m['id']=='capex'),None)
                    if m:
                        if m['value']>0 or m['previousValue']>0:output.remove(m)
                        else:
                            m['value']=-m['value'];m['previousValue']=-m['previousValue']
                            m['changePercent']=round((m['value']-m['previousValue'])/abs(m['previousValue'])*100,2) if m['previousValue'] else None
                            m['accountingBasis']+='; outflows displayed as positive uses of cash; excludes noncash acquisitions'
        text=pages.get(6,'')
        if 'Unaudited condensed consolidated balance sheets' in text and '(in millions of U.S. dollars)' in text and 'As of December 31, 2025* As of June 30, 2026' in text:
            rows=re.findall(r'^Cash and cash equivalents ('+TOKEN+r') ('+TOKEN+r')$',text,re.M)
            if len(rows)==1:add('cash','מזומנים ושווי מזומנים',rows[0][1],rows[0][0],'Cash and cash equivalents',6,instant=('2026-06-30','2025-12-31'),definition='US GAAP balance sheet cash excluding restricted cash; June 2026 vs December 2025, not YoY flow')
            current=re.findall(r'^Debt, current ('+TOKEN+r') ('+TOKEN+r')$',text,re.M)
            longterm=re.findall(r'^Debt, non-current ('+TOKEN+r') ('+TOKEN+r')$',text,re.M)
            if len(current)==len(longterm)==1:
                a,b=current[0],longterm[0]
                add('debt','חוב שוטף ולא שוטף',str(number(a[1])+number(b[1])),str(number(a[0])+number(b[0])),'Debt, current + Debt, non-current',6,instant=('2026-06-30','2025-12-31'),definition='US GAAP sum of current and non-current debt; excludes separately presented operating lease liabilities; not YoY flow')
                m=next(m for m in output if m['id']=='debt');m['sourceRaw']=a[1]+' + '+b[1];m['sourcePreviousRaw']=a[0]+' + '+b[0]
    elif cid=='candidate-sandisk':
        tables=[t for t in doc['tables'] if t['rows'][:3]==[
            ['SANDISK CORPORATION'],['CONSOLIDATED STATEMENTS OF OPERATIONS'],
            ['(in millions, except per share amounts; unaudited)']]
            and t['rows'][3:5]==[['','Three Months Ended','','Year Ended'],
            ['', 'July 3 , 2026', '', 'June 27 , 2025', '', 'July 3 , 2026', '', 'June 27 , 2025']]]
        if len(tables)==1:
            for key,label,source in [('grossProfit','רווח גולמי GAAP','Gross profit'),('netIncome','רווח נקי GAAP','Net income (loss)')]:
                rows=[r for r in tables[0]['rows'] if r and r[0]==source]
                if len(rows)==1 and len(rows[0])==16:
                    r=rows[0];add(key,label,r[2]+r[3],r[6]+r[7],source)
    elif cid=='us-meta-nasdaq-a':
        for title, specs in [
            ('CONDENSED CONSOLIDATED STATEMENTS OF INCOME', [('netIncome','רווח נקי GAAP','Net income'),('operatingIncome','רווח תפעולי GAAP','Income from operations')]),
            ('CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS', [('operatingCash','תזרים תפעולי','Net cash provided by operating activities'),('capex','רכישת רכוש וציוד במזומן','Purchases of property and equipment')])]:
            tables=[t for t in doc['tables'] if len(t['rows'])>6 and t['rows'][0][0]=='META PLATFORMS, INC.' and t['rows'][1][0]==title
                and t['rows'][4][:4]==['','Three Months Ended September 30,','','Nine Months Ended September 30,']
                and t['rows'][5][:8]==['','2026','','2025','','2026','','2025']]
            if len(tables)!=1:continue
            for key,label,source in specs:
                rows=[r for r in tables[0]['rows'] if r and r[0]==source]
                if len(rows)==1 and len(rows[0]) in (8,9):
                    r=rows[0]
                    # CAPEX is a positive cash use; includes only the named row.
                    a,b=r[1],r[3]
                    if key=='capex':
                        if number(a) is None or number(b) is None or number(a)>0 or number(b)>0:continue
                        a,b=str(-number(a)),str(-number(b))
                    add(key,label,a,b,title+': '+source,definition=('US GAAP cash PPE purchases only; excludes finance-lease principal; cash outflows presented positive' if key=='capex' else None))
                    if key=='capex':
                        m=next((m for m in output if m['id']==key),None)
                        if m:m['sourceRaw']=r[1];m['sourcePreviousRaw']=r[3]
    elif cid=='us-lmnd-nyse-common':
        tables=[t for t in doc['tables'] if t.get('page')==11 and any('($ in millions, except Premium per customer)' in ' '.join(r) for r in t['rows'])]
        if len(tables)!=1:return output
        for source,key,label,basis,instant in [
            ('Net loss','netIncome','הפסד נקי GAAP','US GAAP net loss',None),
            ('Adjusted EBITDA','adjustedEbitda','EBITDA מתואם (Non-GAAP)','Issuer-defined Non-GAAP Adjusted EBITDA; not net income or operating cash',None),
            ('Gross earned premium','grossEarnedPremium','פרמיה שהורווחה ברוטו','Gross earned premium, before reinsurance; not GAAP revenue',None),
            ('In force premium (end of period)','inForcePremium','פרמיות בתוקף בסוף התקופה','Annualized premium at period end incl placed business; operational KPI, not recognized revenue',('2026-06-30','2025-06-30'))]:
            rows=[r[0] for r in tables[0]['rows'] if r and r[0].startswith(source+' $ ')]
            if len(rows)!=1:continue
            match=re.fullmatch(re.escape(source)+r'\s+\$\s+('+TOKEN+r')\s+\$\s+('+TOKEN+r')\s+\$\s+('+TOKEN+r')\s+\$\s+('+TOKEN+r')',rows[0])
            if match:add(key,label,match[1],match[2],source,11,definition=basis+'; Q2 2026/2025 shareholder letter USD millions',instant=instant)
        ratio=[r[0] for r in tables[0]['rows'] if r and r[0].startswith('Gross loss ratio ')]
        if len(ratio)==1:
            m=re.fullmatch(r'Gross loss ratio (\d+) % (\d+) % (\d+) % (\d+) %',ratio[0])
            if m and all(0<=int(v)<=1000 for v in m.groups()):
                add('grossLossRatio','יחס הפסדים ברוטו',m[1],m[2],'Gross loss ratio',11,definition='Issuer gross loss ratio Q2 2026/Q2 2025; percent, not net loss ratio or profit margin')
                next(v for v in output if v['id']=='grossLossRatio')['unit']='percent'
    elif cid=='candidate-enlight':
        pages={p['page']:p['text'] for p in doc.get('sourcePdfPages',[])}
        for page,key,label,source,pattern in [
            (16,'operatingIncome','רווח תפעולי IFRS','Operating profit',r'Operating profit\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')'),
            (16,'netIncome','רווח לתקופה כולל מיעוט','Profit for the period',r'('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+Profit for the period\s+Profit for the period attributed'),
            (19,'operatingCash','תזרים תפעולי','Net cash from operating activities',r'Net cash from operating activities\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')')]:
            text=re.sub(r'\s+',' ',pages.get(page,''))
            if page==19 and not ('Consolidated Statements of Cash Flows' in text and re.search(r'For the six months ended For the three months ended June 30 June 30 2026 2025 2026 2025 USD in USD in USD in USD in Thousands Thousands Thousands Thousands',text)):continue
            matches=list(re.finditer(pattern,text))
            if len(matches)==1:add(key,label,matches[0][3],matches[0][4],source,page,1000,definition='Consolidated IFRS '+source+'; Q2 not H1; USD thousands to millions; includes tax-benefit accounting')
    elif cid=='candidate-gilat-telecom':
        text=re.sub(r'\s+',' ',next((p['text'] for p in doc.get('sourcePdfPages',[]) if p['page']==6),''))
        # Reviewed RTL layout: annual 2025, Q2 2025, Q2 2026, H1 2025, H1 2026.
        for key,label,pattern,basis in [
            ('operatingIncome','רווח מפעולות רגילות',r'תולועפמ חוור\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+תוליגר','IFRS profit from ordinary operations'),
            ('netIncome','רווח לתקופה',r'\)דספה\( חוור\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+הפוקתל','IFRS profit for period'),
            ('adjustedEbitda','EBITDA מתואם (Non-IFRS)',r'EBITDA\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+('+TOKEN+r')\s+ADJUSTED','Issuer adjusted EBITDA excluding IFRS16 satellite lease depreciation effect; not IFRS profit')]:
            m=list(re.finditer(pattern,text))
            if len(m)==1:add(key,label,m[0][3],m[0][2],label,6,1000,definition=basis+'; original board report Q2 ILS thousands to millions')
    return output


def iren_original(doc):
    """FY2026 issuer HTML; annual columns only, never adjacent QoQ columns."""
    if doc.get('companyId')!='candidate-iren' or doc.get('format')!='html' or doc.get('title') not in ('IREN Reports FY26 Results','IREN Reports FY26 Results | IREN'):return []
    tables=doc.get('tables',[])
    annual=[t for t in tables if t['rows'][:2]==[['US$m','Year ended','','Year ended',''],['June 30, 2026 1','','June 30, 2025','']]]
    ops=[t for t in annual if ['Revenue','',''] in t['rows']]
    flows=[t for t in annual if ['Cash flow from operating activities','',''] in t['rows']]
    if len(ops)!=1 or len(flows)!=1:return []
    result=[]
    def row(t,label):
        r=[r for r in t['rows'] if r and r[0]==label]
        if len(r)!=1 or len(r[0])!=5:return None
        a,b=r[0][1].replace(' ',''),r[0][3].replace(' ','')
        return (a,b) if number(a) is not None and number(b) is not None else None
    def add(key,label,values,source,basis):
        if not values:return
        a,b=values
        m=_proposal(doc,key,label,number(a),number(b),a,b,'2025-07-01','2026-06-30','2024-07-01','2025-06-30','USD million',basis,source,None,'retained-issuer-html-table')
        if m:result.append(m)
    for key,label,source in [('revenue','הכנסות','Total Revenue'),('aiRevenue','הכנסות שירותי AI','AI Cloud Services Revenue'),('netIncome','רווח/הפסד נקי','Net income (loss)')]:
        add(key,label,row(ops[0],source),source,'US GAAP FY2026/FY2025 issuer statement; US$m; historical, not a new quarter')
    add('operatingCash','תזרים תפעולי',row(flows[0],'Net cash from (used in) operating activities'),'Net cash from (used in) operating activities','Reported FY2026/FY2025 operating cash including customer advances')
    a=row(flows[0],'Payments for property, plant and equipment net of computer hardware');b=row(flows[0],'Payments for computer hardware')
    if a and b and all(number(v)<=0 for v in a+b):
        add('capex','השקעות PPE וחומרה במזומן',tuple(str(-(number(a[i])+number(b[i]))) for i in (0,1)),'Payments for PPE net of computer hardware + Payments for computer hardware','FY2026/FY2025 cash PPE plus hardware only; excludes intangibles, deposits and noncash additions')
        result[-1]['sourceRaw']=a[0]+' + '+b[0];result[-1]['sourcePreviousRaw']=a[1]+' + '+b[1]
    return result if all(any(m['id']==k for m in result) for k in ('revenue','operatingCash','capex')) else []
