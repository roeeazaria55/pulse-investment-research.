"""Auditable evidence-capped ranking, separate from sentiment or stock prediction."""
import hashlib
import re
from collect_articles import relevant, contains, normalized

VERSION='evidence-3.2'
EVENTS=[
    ('results','תוצאות כספיות',75,['financial results','quarter results','earnings results','דוחות כספיים','תוצאות כספיות']),
    ('guidance','שינוי תחזית',75,['raises guidance','cuts guidance','lowers guidance','raises outlook','cuts outlook','העלאת תחזית','הורדת תחזית']),
    ('financing','מימון או גיוס',65,['financing','debt offering','capital raise','raises capital','credit facility','גיוס הון','מימון']),
    ('transaction','עסקה או רכישה',65,['acquires','acquisition','merger','signs agreement','signs deal','רכישה','מיזוג','הסכם']),
    ('regulatory','החלטה רגולטורית או הליך',70,['fda clears','fda approves','regulatory approval','court orders','court ruling','אישור רגולטורי','החלטת בית משפט']),
]
OPINION=['price target','target price','buy rating','bull case','bear case','is a buy','undervalued','overvalued','here is why','here s why','יעד מחיר','המלצת קנייה','כדאי לקנות']
EDITORIAL=['Reuters','Associated Press','AP News','CNBC','Financial Times','Bloomberg','The Wall Street Journal','גלובס','כלכליסט','TheMarker']

def rate(item, company=None):
    title=item['headline']
    match=company is None or relevant(title,company)
    direct=bool(company and any(contains(title,a) for a in company['distinctiveAliases']))
    sec=item.get('sourceId','').startswith('sec-') and item.get('sourceUrl','').startswith('https://www.sec.gov/Archives/')
    if sec:match=True;direct=True
    official=sec or item.get('verifiedOfficial',False)
    event,label,potential='general','עדכון למעקב',25
    opinion=any(contains(title,x) for x in OPINION)
    for kind,he,points,terms in EVENTS:
        if any(contains(title,t) for t in terms):event,label,potential=kind,he,points;break
    position_flow=bool(re.search(r'\b(?:acquires|buys|sells|reduces|increases|raises|boosts|cuts|trims|new)\b.{0,70}\b(?:shares of|shares in|stake in|holdings in|investment in|position in)\b',title,re.I))
    future_results=any(x in title.lower() for x in ('to report','to announce','timing of','announces date','schedules')) and any(x in title.lower() for x in ('results','earnings'))
    if future_results:event,label,potential='results-schedule','הודעה על מועד דוח עתידי',30
    if position_flow:event,label,potential='investor-position','שינוי אחזקה של משקיע אחר',15
    if sec and any(x in item.get('classification',{}).get('rule','') for x in ('annual','quarter','financial','periodic-report')):
        event,label,potential='results','מסמך תוצאות רשמי',85
    if opinion:event,label,potential='opinion','דעה או יעד מחיר',15
    if not match:potential=0
    score=potential if official else min(potential,55)
    level='high' if score>=75 and official and match and not opinion else 'medium' if score>=40 else 'low'
    authority='official-verified' if official else 'attributed-editorial' if item.get('publisher') in EDITORIAL else 'attributed-unverified'
    reliability='גבוהה למקור הראשוני, ללא אימות עצמאי לתוכן' if official else 'ייחוס למערכת חדשות; הכתבה לא אומתה' if authority=='attributed-editorial' else 'ייחוס הספק בלבד; אמינות התוכן טרם אומתה'
    confidence='high' if official and match else 'medium' if match and direct else 'low'
    reason=(f'{label}: עדיפות למחקר לפי סוג האירוע, לא תחזית לתנועת המניה. ' if match else 'הכותרת אינה עומדת בכללי שיוך החברה. ')
    reason+=('מקור ראשוני אומת; יש לקרוא את המסמך בהקשרו.' if official else 'הבסיס הוא כותרת ומטא־נתונים בלבד, לכן אין דירוג גבוה גם כשנזכר אירוע מהותי.')
    if opinion:reason+=' יעד מחיר או דעה אינם ראיה לאירוע מהותי.'
    if position_flow:reason+=' רכישת מניות בידי משקיע אחר אינה עסקה שביצעה החברה.'
    if future_results:reason+=' זו הודעה על מועד עתידי, לא פרסום התוצאות עצמן.'
    return {'version':VERSION,'eventKind':event,'eventLabel':label,'eventScore':score,'potentialMateriality':potential,
            'level':level,'sourceAuthority':authority,'sourceReliability':reliability,'companyRelevance':'direct' if direct else 'context' if match else 'rejected',
            'confidence':confidence,'basis':'official-metadata' if official else 'headline-only','verifiedOfficial':official,
            'independentConfirmations':0,'why':reason,'evidenceUrls':[item['sourceUrl']]}

def group_events(items, ratings):
    groups=[]
    stop={'the','and','for','with','from','stock','shares','company','a','to','of','in','on','as','by','its','is'}
    for item in items:
        title=item['headline'].rsplit(' - ',1)[0]
        tokens=set(normalized(title).split())-stop
        kind=ratings[item['id']]['eventKind']
        day=(item.get('publishedAt') or '')[:10]
        existing=None
        for g in groups:
            same=(g['securityId']==item.get('securityId') and g['eventKind']==kind and g['publicationDay']==day)
            similarity=len(tokens&g['_tokens'])/max(1,len(tokens|g['_tokens']))
            # Conservatively merge near-identical headlines only; never infer independent corroboration.
            if same and similarity>=0.86:existing=g;break
        if existing:existing['itemIds'].append(item['id']);continue
        key=item.get('securityId','')+'|'+kind+'|'+normalized(title)
        groups.append({'id':'event:'+hashlib.sha256(key.encode()).hexdigest()[:24],
                       'securityId':item.get('securityId'),'eventKind':kind,'publicationDay':day,
                       'itemIds':[item['id']],'independentConfirmations':0,
                       'groupingBasis':'near-identical-headlines-not-independent-confirmations','_tokens':tokens})
    return [{k:v for k,v in g.items() if k!='_tokens'} for g in groups]
