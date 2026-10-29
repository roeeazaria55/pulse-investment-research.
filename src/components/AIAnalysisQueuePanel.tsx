import {useEffect,useState} from 'react';
import {Clock3,LockKeyhole,AlertTriangle,FileSearch} from 'lucide-react';
import registry from '../../public/data/official-registry.json';

export type AIQueueJob={id:string;candidateId:string;companyId:string;ticker:string;sourceUrl:string;
 sourceSha256:string;candidatePayloadSha256:string;reportPeriod:string|null;createdAt:string;updatedAt:string;
 status:string;statusReason:string;attempts:number;analysisExecuted:boolean;
 publicationStatus:'not-approved';approvedModelChange:false;history:{status:string;at:string}[]};
export type AIQueueStore={version:1;jobs:AIQueueJob[];latestByCompany:Record<string,string>};
const hosts:Record<string,string[]>=Object.fromEntries(registry.companies.map(c=>[c.id,c.allowedHosts]));
const statuses=new Set(['detected','validated','queued','processing','draft-ready','pending-review','approved',
 'published','blocked','failed','pending-budget','rejected','superseded']);
const descriptions:Record<string,string>={
 'queued':'מוכן להכנת ניתוח — AI טרם הופעל',
 'blocked':'חסום: דורש השלמת מקור או אימות נתונים',
 'pending-budget':'ממתין לתקציב AI',
 'processing':'ניתוח בביצוע',
 'draft-ready':'טיוטה מוכנה',
 'pending-review':'טיוטה ממתינה לאישור',
 'approved':'אושר בתהליך מוגן',
 'published':'מחקר פורסם',
 'failed':'נדרש טיפול בכשל',
 'superseded':'הוחלף בגרסת מקור חדשה',
 'rejected':'טיוטה נדחתה',
 'validated':'אומת מקור',
 'detected':'זוהה דוח'
};
function allowed(url:string,id:string){
 try{const p=new URL(url);return p.protocol==='https:'&&!p.username&&!p.password&&!p.port&&hosts[id]?.includes(p.hostname);}
 catch{return false;}
}
export function validateAIQueueStore(value:unknown):AIQueueStore{
 if(!value||typeof value!=='object')throw Error('תור AI אינו תקין');
 const v=value as AIQueueStore;
 if(v.version!==1||!Array.isArray(v.jobs)||v.jobs.length>1000||!v.latestByCompany||typeof v.latestByCompany!=='object')
  throw Error('תור AI אינו תקין');
 const ids=new Set<string>();
 for(const j of v.jobs){
  if(!j||typeof j!=='object'||!/^ai-job:[a-f0-9]{32}$/.test(j.id)||ids.has(j.id)||
     !/^earnings-candidate:[a-f0-9]{32}$/.test(j.candidateId)||
     !/^[a-f0-9]{64}$/.test(j.sourceSha256)||!/^[a-f0-9]{64}$/.test(j.candidatePayloadSha256)||
     !allowed(j.sourceUrl,j.companyId)||!statuses.has(j.status)||!Number.isInteger(j.attempts)||
     j.attempts<0||j.attempts>5||j.publicationStatus!=='not-approved'||j.approvedModelChange!==false||
     typeof j.analysisExecuted!=='boolean'||!Array.isArray(j.history)||!j.history.length||
     j.history[j.history.length-1]?.status!==j.status||
     !Number.isFinite(Date.parse(j.createdAt))||!Number.isFinite(Date.parse(j.updatedAt)))
   throw Error('תור כולל רשומה לא מאומתת');
  ids.add(j.id);
 }
 for(const [company,id] of Object.entries(v.latestByCompany)){
  if(!v.jobs.some(j=>j.companyId===company&&j.id===id))throw Error('הפניה לטיוטה שאינה קיימת');
 }
 return v;
}
export function AIAnalysisQueuePanel({companyId,compact=false}:{companyId?:string;compact?:boolean}){
 const [store,setStore]=useState<AIQueueStore|null>(null);
 const [error,setError]=useState(false);
 useEffect(()=>{
  let live=true;setStore(null);setError(false);
  fetch(import.meta.env.BASE_URL+'data/ai-analysis-queue.json',{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Queue not yet available');return validateAIQueueStore(await r.json());})
   .then(d=>{if(live)setStore(d);})
   .catch(()=>{if(live)setError(true);});
  return ()=>{live=false;};
 },[]);
 const rows=store?.jobs.filter(j=>(!companyId||j.companyId===companyId)&&
  store.latestByCompany[j.companyId]===j.id) ||[];
 const pending=rows.filter(j=>!['published','rejected','superseded'].includes(j.status));
 return <section className={'pulse-ai-queue'+(compact?' pulse-ai-queue-compact':'')} aria-label="תור מחקר אוטומטי" dir="rtl">
  <div className="pulse-ai-queue-head">
   <div><span className="pulse-ai-kicker">EARNINGS / EVENT QUEUE</span>
    <h4><FileSearch size={19} aria-hidden="true"/> דוחות שממתינים לניתוח</h4></div>
   <span className="pulse-ai-pill"><LockKeyhole size={14}/> ללא הפעלת AI אוטומטית</span>
  </div>
  {store===null&&!error&&<p role="status">טוען תור ניתוחים…</p>}
  {error&&<p role="status">נתוני תור הניתוחים טרם פורסמו. קליטת הדוחות הקיימת לא נפגעה.</p>}
  {store&&<p className="pulse-ai-queue-summary">משימות נוכחיות: <bdi>{rows.length}</bdi> · לטיפול: <bdi>{pending.length}</bdi>. נתוני התור אינם ניתוח השקעה.</p>}
  {!!rows.length&&<div className="pulse-ai-queue-items">{rows.slice(0,compact?4:12).map(j=><div className="pulse-ai-queue-item" key={j.id}>
   <div><strong><bdi>{j.ticker}</bdi></strong><span><bdi>{j.reportPeriod||'תקופה בבדיקה'}</bdi></span></div>
   <p>{descriptions[j.status]||'סטטוס לא מוכר'}</p>
   <a href={j.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={'מקור רשמי עבור '+j.ticker}>
    מקור רשמי <Clock3 size={13}/></a>
  </div>)}</div>}
  {store&&rows.length===0&&<p>אין כרגע משימות ניתוח נתמכות לחברה או לסינון שבחרת.</p>}
  {store&&rows.some(j=>j.status==='blocked')&&<p className="pulse-ai-queue-warning"><AlertTriangle size={16}/> דוח חסום מחייב אימות מקור; לא יפעיל AI.</p>}
  {!store&&error&&<small>הפעלת מפתח API לא נדרשת כדי לראות את התור, לאחר שגרסת הקוד תאושר לפרסום.</small>}
 </section>;
}
