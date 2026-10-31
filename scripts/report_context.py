"""Bounded verbatim report excerpts, never accounting or legal conclusions."""
import hashlib
import re
TOPICS={
 'liquidity':r'liquidity|working capital|credit facilit|debt matur|covenants?|נזילות|אמות מידה',
 'cashFlow':r'cash flows?|capital expenditure|תזרים|השקעות הוניות',
 'outlook':r'guidance|business outlook|forward.looking|תחזית',
 'controls':r'material weakness|internal control|audit opinion|בקרה פנימית',
 'legal':r'legal proceedings|litigation|regulatory investigation|הליכים משפטיים',
 'notes':r'commitments and contingencies|related.part|subsequent events|ביאורים|אירועים לאחר',
}
def extract_context(text):
 text=' '.join(text.split());result=[]
 for topic,pattern in TOPICS.items():
  match=re.search(pattern,text,re.I)
  if match:
   start=max(0,match.start()-180);excerpt=text[start:min(len(text),match.end()+500)]
   result.append({'topic':topic,'text':excerpt,'textSha256':hashlib.sha256(excerpt.encode()).hexdigest(),
                  'scope':'keyword-window-not-complete-disclosure','reviewStatus':'pending-review'})
 return result

def validate_context(rows):
 if not isinstance(rows,list) or len(rows)>len(TOPICS):raise ValueError('Unbounded report context')
 seen=set()
 for row in rows:
  if (not isinstance(row,dict) or row.get('topic') not in TOPICS or row['topic'] in seen
      or not isinstance(row.get('text'),str) or not 0<len(row['text'])<=800
      or row.get('textSha256')!=hashlib.sha256(row['text'].encode()).hexdigest()
      or row.get('scope')!='keyword-window-not-complete-disclosure'
      or row.get('reviewStatus')!='pending-review'):
   raise ValueError('Invalid source excerpt')
  seen.add(row['topic'])
 return rows
