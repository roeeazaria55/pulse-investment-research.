import {ContentBadge} from './ContentBadge';
import {useEffect,useState} from 'react';
import {FileClock,History,ShieldCheck} from 'lucide-react';

type Version={
 id:string;companyId:string;ticker:string;pdfPath:string;pdfSha256:string;
 parentVersionId:string|null;researchHeadline:string;publicationStatus:string;
 immutableSha256:string;sourcePacketSha256:string
};
type Store={version:1;versions:Version[];activeByCompany:Record<string,string>};
const hash=/^[a-f0-9]{64}$/;
const vid=/^research-v:[a-f0-9]{32}$/;
export function validateApprovedResearchStore(value:unknown):Store {
 if(!value||typeof value!=='object')throw Error('ארכיון הגרסאות אינו תקין');
 const v=value as Store;
 if(v.version!==1||!Array.isArray(v.versions)||v.versions.length>500||
    !v.activeByCompany||typeof v.activeByCompany!=='object')throw Error('ארכיון הגרסאות אינו תקין');
 const byId=new Map<string,Version>();
 for(const row of v.versions){
  if(!row||!vid.test(row.id)||!hash.test(row.immutableSha256)||!hash.test(row.pdfSha256)||
     !hash.test(row.sourcePacketSha256)||typeof row.researchHeadline!=='string'||
     row.publicationStatus!=='approved-upon-protected-pr-merge'||
     !/^public\/approved-research\/[A-Za-z0-9_-]+\/[a-f0-9]{32}\.pdf$/.test(row.pdfPath)||
     row.parentVersionId!==null&&!vid.test(row.parentVersionId)||
     byId.has(row.id))throw Error('גרסת מחקר לא מאומתת');
  byId.set(row.id,row);
 }
 for(const [company,id] of Object.entries(v.activeByCompany)){
  if(!byId.has(id)||byId.get(id)?.companyId!==company)
   throw Error('מצביע גרסה פעילה שגוי');
 }
 return v;
}
export function ApprovedResearchHistory({companyId}:{companyId:string}){
 const [data,setData]=useState<Store|null>(null);
 const [status,setStatus]=useState<'loading'|'none'|'error'|'ready'>('loading');
 useEffect(()=>{
  let live=true;
  setStatus('loading');setData(null);
  fetch(import.meta.env.BASE_URL+'data/approved-research-versions.json',{cache:'no-store'})
   .then(async response=>{
    if(response.status===404){if(live)setStatus('none');return;}
    if(!response.ok)throw Error('Archive unavailable');
    const parsed=validateApprovedResearchStore(await response.json());
    if(live){setData(parsed);setStatus('ready');}
   })
   .catch(()=>{if(live)setStatus('error');});
  return ()=>{live=false;};
 },[]);
 const active=data?.activeByCompany[companyId];
 const versions=(data?.versions||[]).filter(v=>v.companyId===companyId);
 return <section className="pulse-approved-history" dir="rtl" aria-label="היסטוריית מחקרים מאושרים">
  <div className="pulse-ai-queue-head">
   <h4><History size={18} aria-hidden="true"/> ארכיון מחקר מאושר</h4>
   <span className="pulse-ai-pill"><ShieldCheck size={14}/> GitHub PR מוגן</span>
  </div>
  {status==='loading'&&<p role="status">בודק היסטוריית גרסאות…</p>}
  {status==='none'&&<p>טרם פורסם מחקר במסלול הגרסאות המאובטח. המחקרים וה־PDF הקיימים נשמרים בנפרד וללא שינוי.</p>}
  {status==='error'&&<p role="status">אין אפשרות לאמת את ארכיון הגרסאות כרגע. לא תוצג גרסה בלתי מאומתת.</p>}
  {status==='ready'&&versions.length===0&&<p>לחברה זו עדיין אין גרסאות בארכיון החדש.</p>}
  {!!versions.length&&<ul className="pulse-approved-history-list">{[...versions].reverse().map(v=><li key={v.id}>
   <FileClock size={19} aria-hidden="true"/>
   <div>
    <ContentBadge kind="approved"/><strong>{v.researchHeadline}</strong>
    <small><bdi>{v.id.slice(0,22)}…</bdi> · SHA <bdi>{v.pdfSha256.slice(0,12)}…</bdi></small>
    <small>{v.id===active?'הגרסה הפעילה בארכיון החדש':'גרסה קודמת, זמינה לצפייה'}</small>
   </div>
   <a href={import.meta.env.BASE_URL+v.pdfPath.replace(/^public\//,'')}
      target="_blank" rel="noopener noreferrer"
      aria-label={'פתיחת PDF של גרסת '+v.ticker}>PDF</a>
  </li>)}</ul>}
  <small>שחזור גרסה מתבצע רק באמצעות Workflow מוגן ו־PR מאושר; אין כפתור פרסום בדפדפן.</small>
 </section>;
}
