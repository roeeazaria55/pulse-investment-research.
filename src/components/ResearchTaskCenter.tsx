import {useEffect,useState} from 'react';
import {officialRegistry} from '../data/official';
import {parseReportIntake,type ReportIntakeSnapshot} from '../data/reportIntake';
import {publishedResearch} from '../data/publishedResearch';
import {researchTarget} from '../research/researchTarget';
import {modelReviewSignals} from '../research/modelReviewSignals';
import {prioritizeTasks,reviewSignalTask,type ResearchTask,type ResearchDestination} from '../research/researchTasks';
import {classifyResearchAlert} from '../research/alertPolicy';
import type {News} from '../types';
import {validateAIReviewFeed,type AIReviewDraft} from './AIReviewDraftPanel';
import {Modal} from './UI';
import {ContentBadge} from './ContentBadge';
const KEY='pulse.research-tasks.v1',VISIT='pulse.research-last-visit.v1';
function saved():Record<string,string>{try{const v=JSON.parse(localStorage.getItem(KEY)||'{}');const clean:Record<string,string>={};if(v&&typeof v==='object'&&!Array.isArray(v))for(const [k,x] of Object.entries(v).slice(-300))if(k.length<300&&(x==='done'||x==='read'))clean[k]=x;return clean;}catch{return {};}}
export function ResearchTaskCenter({news,onOpen}:{news:readonly News[];onOpen:(companyId:string,destination:ResearchDestination)=>void}){
 const [intake,setIntake]=useState<ReportIntakeSnapshot|null>(null),[drafts,setDrafts]=useState<AIReviewDraft[]>([]),[errors,setErrors]=useState<string[]>([]),[loading,setLoading]=useState(true);
 const [done,setDone]=useState(saved),[all,setAll]=useState(false),[showDone,setShowDone]=useState(false);
 const [since]=useState(()=>{try{return localStorage.getItem(VISIT);}catch{return null;}});
 useEffect(()=>{let live=true;const fetchData=async(path:string)=>{const r=await fetch(import.meta.env.BASE_URL+'data/'+path,{cache:'no-store'});if(!r.ok)throw Error(path);return r.json();};
  Promise.allSettled([fetchData('report-intake.json'),fetchData('ai-research-drafts.json')]).then(results=>{if(!live)return;const failed:string[]=[];
   try{if(results[0].status==='fulfilled')setIntake(parseReportIntake(results[0].value));else throw Error();}catch{failed.push('דוחות');}
   try{if(results[1].status==='fulfilled'){const raw=results[1].value;setDrafts(officialRegistry.companies.flatMap(c=>validateAIReviewFeed(raw,c.id).slice(0,1)));}else throw Error();}catch{failed.push('טיוטות AI');}
   setErrors(failed);setLoading(false);
  });
  try{localStorage.setItem(VISIT,new Date().toISOString());}catch{/* local preference only */}
  return ()=>{live=false;};
 },[]);
 const tasks:ResearchTask[]=[];
 const baselines=publishedResearch.map(p=>({companyId:p.analysis.companyId,ticker:officialRegistry.companies.find(c=>c.id===p.analysis.companyId)?.label||p.analysis.companyId,asOf:p.analysis.asOf,sourceUrls:p.analysis.sourceUrls,horizon:researchTarget(p.analysis.companyId)?.horizon}));
 if(intake){tasks.push(...modelReviewSignals(baselines,intake.documents).map(reviewSignalTask));
  for(const b of baselines){const d=intake.documents.filter(d=>d.companyId===b.companyId&&d.status==='read-no-supported-data'&&d.publishedDate&&d.publishedDate>b.asOf&&d.publishedDate<=new Date().toISOString().slice(0,10)).sort((a,b)=>b.publishedDate!.localeCompare(a.publishedDate!))[0];if(d)tasks.push({id:'source:'+b.companyId+':'+d.sha256,kind:'source',companyId:b.companyId,ticker:b.ticker,title:`בדיקת דוח ${b.ticker}`,reason:'הדוח נקרא, אך אין מספיק נתונים מובנים לניתוח.',date:d.publishedDate!,destination:'sources',sourceUrl:d.url});}}
 for(const d of drafts)tasks.push({id:d.id,kind:'ai',companyId:d.companyId,ticker:d.ticker,title:`טיוטת ${d.ticker} מוכנה לבדיקה`,reason:d.fullResearch?.headline||'הניתוח ממתין לבדיקת המקורות והמסקנות.',date:d.firstRecordedAt,destination:'ai'});
 for(const n of news){const alert=classifyResearchAlert(n);if(!alert||alert.severity!=='high')continue;const c=officialRegistry.companies.find(c=>c.ticker&&c.ticker===n.ticker||c.name===n.company||c.label===n.company);if(c)tasks.push({id:'event:'+n.id,kind:'event',companyId:c.id,ticker:c.label,title:`אירוע למחקר ${c.label}`,reason:n.headline,date:n.publishedAt||n.collectedAt,destination:'overview',sourceUrl:n.sourceUrl});}
 const pending=prioritizeTasks(tasks,done),visible=all?(showDone?tasks:pending):pending.slice(0,3);
 const update=(id:string,value:string)=>{const next=Object.fromEntries(Object.entries({...done,[id]:value}).slice(-300));setDone(next);try{localStorage.setItem(KEY,JSON.stringify(next));}catch{/* session only */}};
 const rows=<>{loading&&<p role="status">טוען עדכוני מחקר…</p>}{errors.length>0&&<p role="status">מידע חלקי: {errors.join(' ו־')} אינם זמינים כרגע.</p>}
  {!loading&&!visible.length&&<p>אין משימות פתוחות במידע הזמין. כיסוי המקורות עשוי להיות חלקי.</p>}
  <ul className="research-task-list">{visible.map(t=><li key={t.id}>
   <div className="research-task-meta"><ContentBadge kind={t.kind==='ai'?'ai-draft':t.kind==='model'?'baseline':'source-pending'}/>{since&&t.date>since&&<span>חדש מאז הביקור הקודם</span>}{done[t.id]==='done'&&<span>טופל במכשיר הזה</span>}</div>
   <h3>{t.title}</h3><p>{t.reason}</p><div className="review-inbox-actions"><button type="button" onClick={()=>{setAll(false);onOpen(t.companyId,t.destination);}}>פתיחת {t.kind==='ai'?'הטיוטה':t.kind==='model'?'המודל':'הבדיקה'}</button>{t.sourceUrl&&<a href={t.sourceUrl} target="_blank" rel="noopener noreferrer">למקור ↗</a>}<button type="button" className="text-button" onClick={()=>update(t.id,done[t.id]==='done'?'read':'done')}>{done[t.id]==='done'?'החזרה למעקב':'סימון כטופל'}</button></div>
  </li>)}</ul></>;
 return <section className="panel research-task-center" aria-label="מרכז משימות מחקר"><div className="review-inbox-head"><h2>מה השתנה ומה לבדוק?</h2><span>{pending.length} משימות פתוחות</span></div><p>עד שלושה דברים להתמקד בהם. טיפול במשימה אינו אישור מחקר או שינוי במודל.</p>{!all&&rows}<button type="button" onClick={()=>setAll(true)}>לכל משימות המחקר</button>{all&&<Modal title="משימות המחקר" close={()=>setAll(false)}><label><input type="checkbox" checked={showDone} onChange={e=>setShowDone(e.target.checked)}/> הצגת משימות שטופלו</label>{rows}<small>הסימון נשמר רק במכשיר הזה.</small></Modal>}</section>;
}
