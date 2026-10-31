import {officialRegistry} from '../data/official';
import {useState} from 'react';
import {publishedResearch} from '../data/publishedResearch';
import {researchTarget} from '../research/researchTarget';
import {useReportIntake} from '../hooks/useReportIntake';
import {modelReviewSignals} from '../research/modelReviewSignals';
const KEY='pulse.model-review-read.v1';
function readIds():string[]{try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v.filter((x:unknown)=>typeof x==='string').slice(-200):[];}catch{return [];}}
export function ModelReviewInbox({companyId,onOpen}:{companyId?:string;onOpen:(companyId:string)=>void}){
 const {data,failed}=useReportIntake(companyId||'all');
 const [read,setRead]=useState(readIds);
 const signals=data?modelReviewSignals(publishedResearch.map(p=>({companyId:p.analysis.companyId,ticker:officialRegistry.companies.find(c=>c.id===p.analysis.companyId)?.label||p.analysis.companyId,asOf:p.analysis.asOf,sourceUrls:p.analysis.sourceUrls,horizon:researchTarget(p.analysis.companyId)?.horizon})),data.documents).filter(s=>!companyId||s.companyId===companyId):[];
 const unread=signals.filter(s=>!read.includes(s.id));
 const mark=(id:string)=>{const next=[...read,id].slice(-200);setRead(next);try{localStorage.setItem(KEY,JSON.stringify(next));}catch{/* Current session still works. */}};
 return <section className="model-review-inbox panel" aria-label="בדיקת עדכניות מודל">
  <div className="review-inbox-head"><h3>מה דורש בדיקת מודל?</h3><span>{unread.length?`${unread.length} לבדיקה`:'מעקב מחקר'}</span></div>
  {failed?<p role="status">מצב המקורות אינו זמין. לא ניתן לקבוע אם נדרשת בדיקה.</p>:!data?<p role="status">בודק עדכוני דוחות…</p>:unread.length?<>
   <p className="muted">סיבה לבדוק את ההנחות, לא קביעה שמחיר היעד השתנה.</p>
   <ul>{unread.slice(0,3).map(s=><li key={s.id}><strong>{s.ticker}</strong><p>{s.reason}</p><small>{s.date}</small><div className="review-inbox-actions"><button type="button" onClick={()=>onOpen(s.companyId)}>בדיקת המודל</button>{s.sourceUrl&&<a href={s.sourceUrl} target="_blank" rel="noopener noreferrer">הדוח הרשמי ↗</a>}<button type="button" className="text-button" onClick={()=>mark(s.id)}>סימון כנקרא</button></div></li>)}</ul>
   {unread.length>3&&<p>ועוד {unread.length-3} חברות. ההתראות מופיעות גם בסקירת כל חברה.</p>}
  </>:<p>{signals.length?'כל ההתראות סומנו כנקראו. המודל עצמו לא עודכן.':'לא זוהה אות חדש במקורות שנקראו. כיסוי המקורות עשוי להיות חלקי.'}</p>}
  {!!signals.length&&<small>סימון כנקרא נשמר במכשיר הזה בלבד; אינו אישור או עדכון למודל.</small>}
 </section>;
}
