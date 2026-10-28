import {useEffect,useState} from 'react';
import registry from '../../public/data/official-registry.json';
import {publishedFor} from '../data/publishedResearch';

type Evidence={id:string;label:string;value:number;unit:string;periodStart:string;periodEnd:string;
 previousValue:number|null;absoluteChange:number|null;percentChange:number|null;comparisonStatus:string;
 sourceUrl:string;sourceSha256:string;reviewStatus:string};
type Candidate={id:string;companyId:string;ticker:string;sourceUrl:string;sourceSha256:string;reportPeriod:string|null;
 publishedDate:string|null;firstCandidateAt:string;status:'needs-review'|'blocked';publicationStatus:'not-approved';
 metrics:Evidence[];analystReviewQuestions:{metricId:string;nextCheck:string;thesisRisk:string;baseline:string}[];
 summary:string;thesisImpact:string;forecastComparisonStatus:string;modelChange:'none';
 scenarioReview:{status:'not-calculated';bear:null;base:null;bull:null;reason:string};aiAnalysisExecuted:false};
type CandidateStore={version:1;candidates:Candidate[];latestByCompany:Record<string,string>};
const hosts:Record<string,string[]>=Object.fromEntries(registry.companies.map(c=>[c.id,c.allowedHosts]));
function sourceLink(url:string,companyId:string){
 try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&hosts[companyId]?.includes(u.hostname)?u.href:null;}
 catch{return null;}
}
export function validateCandidateStore(value:unknown,companyId:string):Candidate[]{
 if(!value||typeof value!=='object')throw Error('פורמט טיוטות לא תקין');
 const data=value as CandidateStore;
 if(data.version!==1||!Array.isArray(data.candidates)||!data.latestByCompany||typeof data.latestByCompany!=='object')
  throw Error('פורמט טיוטות לא תקין');
 const matched=data.candidates.filter(c=>c.companyId===companyId);
 if(matched.length>100)throw Error('יותר מדי טיוטות לחברה');
 const ids=new Set<string>();
 for(const c of matched){
  if(!/^earnings-candidate:[a-f0-9]{32}$/.test(c.id)||ids.has(c.id)||
    !/^[a-f0-9]{64}$/.test(c.sourceSha256)||!sourceLink(c.sourceUrl,c.companyId)||
    !Array.isArray(c.metrics)||!Array.isArray(c.analystReviewQuestions)||
    !['needs-review','blocked'].includes(c.status)||c.publicationStatus!=='not-approved'||
    c.modelChange!=='none'||c.aiAnalysisExecuted!==false||
    c.scenarioReview?.status!=='not-calculated'||c.scenarioReview.bear!==null||
    c.scenarioReview.base!==null||c.scenarioReview.bull!==null||
    !Number.isFinite(Date.parse(c.firstCandidateAt)))throw Error('טיוטה אינה תקינה');
  ids.add(c.id);
  for(const m of c.metrics){
    if(!Number.isFinite(m.value)||m.sourceSha256!==c.sourceSha256||
      m.sourceUrl!==c.sourceUrl||!['pending-review','needs-reconciliation'].includes(m.reviewStatus)||
      (m.previousValue!==null&&!Number.isFinite(m.previousValue))||
      (m.absoluteChange!==null&&!Number.isFinite(m.absoluteChange))||
      (m.percentChange!==null&&!Number.isFinite(m.percentChange)))throw Error('ראיית מדד אינה תקינה');
  }
 }
 if(data.latestByCompany[companyId] && !matched.some(c=>c.id===data.latestByCompany[companyId]))
  throw Error('מזהה הטיוטה הנוכחית אינו קיים');
 return matched.sort((a,b)=>b.firstCandidateAt.localeCompare(a.firstCandidateAt));
}
export function EarningsResearchCandidates({companyId,onPrepare}:{companyId:string;onPrepare?:(prompt:string)=>void}){
 const [items,setItems]=useState<Candidate[]|null>(null);
 const [error,setError]=useState(false);
 useEffect(()=>{
  let active=true;setItems(null);setError(false);
  fetch(import.meta.env.BASE_URL+'data/earnings-research-candidates.json',{cache:'no-store'})
   .then(async res=>{if(!res.ok)throw Error('טיוטות לא פורסמו');return validateCandidateStore(await res.json(),companyId);})
   .then(rows=>{if(active)setItems(rows);})
   .catch(()=>{if(active)setError(true);});
  return ()=>{active=false;};
 },[companyId]);
 const current=items?.[0];
 const baseline=publishedFor(companyId);
 return <section className="thesis-metric" dir="rtl" aria-label="טיוטות עדכון מחקר מדוחות" data-testid="earnings-research-candidates">
  <h4>טיוטות מחקר אוטומטיות · לא מאושרות</h4>
  <p><small>טיוטות נתוני מקור בלבד. אין החלפה אוטומטית של המחקר הקיים, מחירי יעד או משקולות Bear/Base/Bull.</small></p>
  {items===null&&!error&&<p role="status">טוען טיוטות…</p>}
  {error&&<p role="status">טיוטות מחקר עדיין אינן זמינות. המחקר המאושר נשמר ללא שינוי.</p>}
  {items?.length===0&&<p role="status">לא נשמרה טיוטת דוח נתמכת לחברה זו.</p>}
  {current&&<>
   <p><strong>{current.ticker} · {current.reportPeriod||'תקופה לא מאומתת'}</strong> · {current.status==='blocked'?'חסומה לבדיקה':'ממתינה לבדיקת אנליסט'} · {current.metrics.length} מדדים</p>
   <p>מועד פרסום מדווח: {current.publishedDate||'לא אומת'} · זיהוי טיוטה ראשון: <bdi>{new Date(current.firstCandidateAt).toLocaleDateString('he-IL')}</bdi> (לא מועד פרסום).</p>
   {sourceLink(current.sourceUrl,current.companyId)&&<a href={sourceLink(current.sourceUrl,current.companyId)!} target="_blank" rel="noopener noreferrer">מסמך המקור הרשמי</a>}
   <details><summary>הצגת מדדי הדוח ושינויי התקופות ({current.metrics.length})</summary>
    <ul>{current.metrics.map(m=><li key={m.id}>
     <strong>{m.label}:</strong> <bdi>{m.value.toLocaleString('en-US')} {m.unit}</bdi> · <bdi>{m.periodStart}–{m.periodEnd}</bdi>
     {m.absoluteChange!==null?<p>שינוי מול תקופה תואמת: <bdi>{m.absoluteChange.toLocaleString('en-US')} {m.unit}</bdi>
      {m.percentChange!==null&&<> · <bdi>{m.percentChange}%</bdi></>}</p>:<p><small>השוואה חסומה או חסרה; אין Beat/Miss.</small></p>}
     <small>מקור: {m.sourceSha256.slice(0,12)}… · {m.reviewStatus}</small>
    </li>)}</ul>
   </details>
   {!!current.analystReviewQuestions.length&&<details><summary>הנחות שדורשות בחינה במודל הקודם</summary>
    <ul>{current.analystReviewQuestions.map(q=><li key={q.metricId}><strong>{q.metricId}:</strong> {q.nextCheck}
     <p><small>סיכון שנשמר בתזה: {q.thesisRisk}</small></p></li>)}</ul>
   </details>}
   <details><summary>מחקר קיים לעומת טיוטת הדוח (ללא שינוי אוטומטי)</summary>
    {baseline?<div className="report-intake-grid">
      <div className="thesis-metric"><h5>המחקר הציבורי הקיים</h5>
       <p><strong>תזה:</strong> {baseline.analysis.fields.thesis}</p>
       <p><strong>שווי ותרחישים קיימים:</strong> {baseline.analysis.fields.valuation}</p>
      </div>
      <div className="thesis-metric"><h5>הטיוטה שנקלטה · לא אושרה</h5>
       <p>{current.summary}</p>
       <p>{current.metrics.length} מדדים מקוריים; {current.metrics.filter(m=>m.absoluteChange!==null).length} השוואות היסטוריות מתאימות.</p>
       <p>תזת ההשקעה והמודל טרם הוערכו מחדש.</p>
      </div>
     </div>:<p>טרם פורסם מחקר בסיס לחברה זו. נתוני המקור אינם תחליף למחקר מאושר.</p>}
   </details>
   <p><strong>השפעה על התזה:</strong> {current.thesisImpact}</p>
   <p><strong>תחזית ומחיר יעד:</strong> לא עודכנו. {current.scenarioReview.reason}</p>
   {onPrepare&&<button type="button" onClick={()=>onPrepare('בדוק טיוטת מחקר ל־'+current.ticker+
    '\nדוח: '+(current.reportPeriod||'לא ידוע')+'\nמקור: '+current.sourceUrl+
    '\nמדדים ממתינים לאימות: '+current.metrics.map(m=>m.label+': '+m.value+' '+m.unit+' '+m.periodStart+'–'+m.periodEnd).join('; ')+
    '\nהפרד עובדות, חישובים, פרשנות והשערות. אל תעדכן מודל או מחיר יעד בלי אישור.')}>הכן בקשה לבדיקת ניתוח</button>}
   {items&&items.length>1&&<details><summary>היסטוריית טיוטות קודמות ({items.length-1})</summary>
    <ul>{items.slice(1).map(c=><li key={c.id}>{c.reportPeriod||'תקופה לא ידועה'} · {new Date(c.firstCandidateAt).toLocaleDateString('he-IL')} · {c.sourceSha256.slice(0,12)}… · לא אושר</li>)}</ul>
   </details>}
  </>}
  <p><small>אישור ופרסום יבוצעו ב־GitHub PR עם סקירת בעל הרשאה; לא באמצעות כפתור ציבורי באתר.</small></p>
 </section>;
}
