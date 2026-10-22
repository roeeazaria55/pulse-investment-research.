import {useEffect,useState} from 'react';
interface BriefEvidence {observationId:string;metricId:string;value:number;unit:string;raw:string;periodStart:string;periodEnd:string;basis:string;sourceUrl:string;approvalStatus:string;forecastComparisonStatus:string;forecastComparisonReasons?:string[];reviewQuestion:string}
interface Brief {id:string;companyId:string;status:string;period:string;sourceUrl:string;reportPublishedDate:string|null;evidence:BriefEvidence[];thesisImpact:string;valuationAction:string;aiAnalysisEnabled:boolean;missing:string[]}
const labels:Record<string,string>={revenue:'הכנסות',grossProfit:'רווח גולמי',operatingCash:'תזרים תפעולי',capex:'השקעות הוניות'};
export function ResearchUpdateProposal({companyId}:{companyId:string}){
 const [briefs,setBriefs]=useState<Brief[]|null>(null);
 const [error,setError]=useState(false);
 useEffect(()=>{
  if(companyId!=='us-dlo-nasdaq-a')return;
  let alive=true;setBriefs(null);setError(false);
  fetch(import.meta.env.BASE_URL+'data/research-update-proposals.json',{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Proposal data unavailable');return r.json();})
   .then(data=>{if(alive&&data?.version===1&&Array.isArray(data.proposals))setBriefs(data.proposals.filter((p:Brief)=>p.companyId===companyId));else if(alive)setError(true);})
   .catch(()=>{if(alive)setError(true);});
  return ()=>{alive=false;};
 },[companyId]);
 if(companyId!=='us-dlo-nasdaq-a')return null;
 return <section className="report-intake" dir="rtl" aria-label="הצעת עדכון מחקר מבוססת מקורות">
  <h4>הצעת עדכון מחקר · לבדיקה בלבד</h4>
  <p>תדריך אוטומטי המבוסס על נתוני מקור; אינו ניתוח AI ואינו משנה את תזת ההשקעה או מחיר היעד.</p>
  {error&&<p role="status">אין כרגע תדריך מחקר שמור זמין.</p>}
  {!error&&briefs===null&&<p role="status">טוען תדריך מקור…</p>}
  {briefs?.length===0&&<p role="status">לא נמצאו תדריכים לחברה זו.</p>}
  {briefs?.map(b=><article key={b.id}>
   <p><strong>דוח {b.period}</strong> · פרסום {b.reportPublishedDate||'מועד לא מאומת'} · מצב: {b.status==='review-only'?'ממתין לבדיקה':b.status}</p>
   <ul>{b.evidence.map(e=><li key={e.observationId}>
    <strong>{labels[e.metricId]||e.metricId}:</strong> <bdi>{e.value} {e.unit}</bdi> · {e.approvalStatus==='approved'?'אושר':'לא אושר'}
    <p>{e.reviewQuestion}</p>
    <p>השוואת תחזית: {e.forecastComparisonStatus==="comparable"?"נמצאה השוואה מאושרת":e.forecastComparisonStatus==="blocked"?"חסומה": "אין תחזית תואמת מאושרת"}.</p>
    {e.forecastComparisonReasons?.length? <ul>{e.forecastComparisonReasons.map((r,i)=><li key={i}>{r}</li>)}</ul>:null}
   </li>)}</ul>
   <p>{b.thesisImpact}</p><p>{b.valuationAction}</p>
   <p>חסר לפני החלטה: {b.missing.join(' · ')}</p>
   {b.sourceUrl?.startsWith('https://')&&<a href={b.sourceUrl} target="_blank" rel="noopener noreferrer">מסמך המקור ↗</a>}
  </article>)}
 </section>;
}
