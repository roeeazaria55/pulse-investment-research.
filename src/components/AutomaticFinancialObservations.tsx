import {useEffect,useState} from 'react';

export interface AutomaticFinancialObservation {
 id:string;companyId:string;metricId:string;sourceRaw:string;sourceRow:string;
 sourceTable:string;sourceUrl:string;sourceSha256:string;reviewVersionId:string;
 value:number;unit:string;sourceUnit:string;period:string;periodStart:string;periodEnd:string;
 basis:string;collectedAt:string|null;publishedDate:string|null;
 reviewStatus:'pending-review'|'needs-reconciliation';revisedSource:boolean;
}
export interface AutomaticFinancialSnapshot {
 version:number;source:string;observations:AutomaticFinancialObservation[];issues:{companyId:string;metricId:string;reason:string}[];
}
const labels:Record<string,string>={revenue:'הכנסות',grossProfit:'רווח גולמי',operatingCash:'תזרים מפעילות שוטפת',capex:'CAPEX (השקעות מזומן)'};
export function AutomaticFinancialObservations({companyId}:{companyId:string}){
 const [state,setState]=useState<'loading'|'ready'|'error'>('loading');
 const [snapshot,setSnapshot]=useState<AutomaticFinancialSnapshot|null>(null);
 useEffect(()=>{
  let active=true;
  setState('loading');setSnapshot(null);
  fetch(import.meta.env.BASE_URL+'data/auto-financial-observations.json',{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('No saved observations');return await r.json() as AutomaticFinancialSnapshot;})
   .then(data=>{if(!active)return;setSnapshot(data&&data.version===1&&Array.isArray(data.observations)?data:null);setState(data&&data.version===1?'ready':'error');})
   .catch(()=>{if(active)setState('error');});
  return ()=>{active=false;};
 },[companyId]);
 if(companyId!=='us-dlo-nasdaq-a')return null;
 const observations=(snapshot?.observations||[]).filter(o=>o.companyId===companyId);
 const issues=(snapshot?.issues||[]).filter(o=>o.companyId===companyId);
 return <section className="report-intake" dir="rtl" aria-label="נתונים שנקלטו אוטומטית לבדיקת אנליסט">
  <h4>נתוני מקור שנקלטו אוטומטית · ממתינים לבדיקה</h4>
  <p>המדדים חולצו משורות של דוח רשמי שכבר נקרא באוסף המקורות. תצוגה זו אינה אישור חשבונאי ואינה מעדכנת תחזיות או מחירי יעד.</p>
  {state==='loading'&&<p role="status">טוען תור נתונים…</p>}
  {state==='error'&&<p role="status">תור הנתונים האוטומטי אינו זמין. אין להסיק שלא פורסם דוח.</p>}
  {state==='ready'&&observations.length===0&&<p role="status">אין כרגע הצעות מדדים ממקור נתונים שניתן למפות בבטחה.</p>}
  {observations.map(o=><article className="thesis-metric" key={o.id}>
   <h5>{labels[o.metricId]||o.metricId}</h5>
   <p><strong><bdi>{o.value.toLocaleString('en-US',{maximumFractionDigits:6})} {o.unit}</bdi></strong> · <bdi>{o.periodStart}–{o.periodEnd}</bdi></p>
   <p>{o.basis} · מקור: <bdi>{o.sourceRow}</bdi> · ערך גולמי: <bdi>{o.sourceRaw} {o.sourceUnit}</bdi></p>
   <p><strong>{o.reviewStatus==='needs-reconciliation'?'נדרש בירור: מסמך המקור השתנה':'ממתין לבדיקת אנליסט'}</strong> · גרסת מקור: <bdi>{o.sourceSha256.slice(0,12)}…</bdi> · אין השוואת תחזית לפני אישור.</p>
   {o.sourceUrl.startsWith('https://')&&<a href={o.sourceUrl} target="_blank" rel="noopener noreferrer">צפייה בדוח הרשמי ↗</a>}
  </article>)}
  {issues.map((issue,i)=><p key={issue.metricId+'-'+i} role="status">נדרשת בדיקה ל־{labels[issue.metricId]||issue.metricId}: {issue.reason}</p>)}
 </section>;
}
