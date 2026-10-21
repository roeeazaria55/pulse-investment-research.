import {useEffect,useState} from 'react';
import sources from '../data/newResearchSourceManifest.json';

type Page={page:number;text:string};
type PageDocument={pages:Page[]};
function validPages(x:unknown,count:number):x is PageDocument {
 if(!x||typeof x!=='object'||!('pages' in x))return false;
 const pages=(x as {pages:unknown}).pages;
 return Array.isArray(pages)&&pages.length===count&&pages.every((p,i)=>p&&typeof p==='object'&&p.page===i+1&&typeof p.text==='string'&&p.text.length>0&&p.text.length<100000);
}
/** Reads committed extracted pages only; the manifest is not proof of deployment. */
export function UnverifiedFullResearch({companyId}:{companyId:string}){
 const source=sources.research.find(r=>r.companyId===companyId);
 const [pages,setPages]=useState<Page[]|null>(null);
 const [status,setStatus]=useState<'idle'|'loading'|'missing'|'ready'>('idle');
 useEffect(()=>{setPages(null);setStatus('idle');},[companyId]);
 if(!source)return null;
 const load=async()=>{
  setStatus('loading');
  try{
   const url=import.meta.env.BASE_URL+'research-pages/'+encodeURIComponent(source.ticker)+'.pages.json';
   const response=await fetch(url,{cache:'no-store'});
   if(!response.ok)throw Error('not published');
   if(Number(response.headers.get('content-length')||0)>250000)throw Error('too large');
   const raw=await response.text();if(raw.length>250000)throw Error('too large');
   const doc:unknown=JSON.parse(raw);
   if(!validPages(doc,source.pages))throw Error('invalid page structure');
   setPages(doc.pages);setStatus('ready');
  }catch{setPages(null);setStatus('missing');}
 };
 return <details className="research-import-info" data-testid="unverified-full-reading">
  <summary>קריאת כל עמודי מחקר המקור · {source.ticker}</summary>
  <p>זהו חילוץ טקסט אוטומטי ממסמך מחקר שסופק על ידי המשתמש. סדר עמודות בעברית עלול להשתבש. קובץ ה־PDF המקורי הוא המקור הקובע; הנתונים אינם מאומתים מול דיווחי החברה.</p>
  {status==='idle'&&<button type="button" onClick={()=>void load()}>טעינת עמודי המחקר</button>}
  {status==='loading'&&<p role="status">טוען את מסמך המחקר…</p>}
  {status==='missing'&&<><p role="alert">קובצי עמודי המחקר טרם פורסמו במאגר או שלא עברו אימות. לא יוצג תוכן חלקי.</p><button type="button" onClick={()=>void load()}>בדיקה חוזרת</button></>}
  {status==='ready'&&pages&&<div>{pages.map(page=><section key={page.page} className="analysis-field-preview" aria-label={'עמוד '+page.page}>
   <h4>עמוד {page.page} מתוך {pages.length}</h4>
   <pre dir="auto" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',fontFamily:'inherit',lineHeight:1.7}}>{page.text}</pre>
  </section>)}</div>}
 </details>;
}
