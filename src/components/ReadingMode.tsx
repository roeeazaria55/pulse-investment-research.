import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Modal} from './UI';
interface Chapter {id:string;label:string}
const FONT='pulse.reader.font.v1';
function load(key:string){try{return localStorage.getItem(key)||'';}catch{return '';}}
export function ReadingMode({id,title,chapters,children}:{id:string;title:string;chapters:readonly Chapter[];children:ReactNode}){
 const key='pulse.reader.position.v1:'+id,root=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null);
 const [open,setOpen]=useState(false),[font,setFont]=useState(()=>{const n=Number(load(FONT));return [16,18,20,22].includes(n)?n:18;});
 const [resume,setResume]=useState(()=>load(key));
 const [position,setPosition]=useState('');
 useEffect(()=>{setResume(load(key));setPosition('');},[key]);
 const remember=(anchor:string)=>{setPosition(anchor);try{localStorage.setItem(key,anchor);}catch{/* Reading remains available. */}};
 const go=(anchor:string)=>{const target=root.current?.querySelector<HTMLElement>('[id="'+anchor.replace(/["\\]/g,'')+'"]');if(!target)return;const detail=target.closest('details');if(detail)detail.open=true;target.focus({preventScroll:true});target.scrollIntoView({block:'start'});remember(anchor);};
 useEffect(()=>{if(typeof IntersectionObserver==='undefined'||!root.current)return;
  const observer=new IntersectionObserver(entries=>{const near=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(near&&near.target.id)remember(near.target.id);},{rootMargin:'-10% 0px -65% 0px'});
  root.current.querySelectorAll('[data-reading-anchor]').forEach(e=>observer.observe(e));return()=>observer.disconnect();
 },[id,open]);
 const savedChapter=chapters.find(c=>c.id===resume);
 const content=<div className="reading-mode-content" ref={root} style={{'--reading-size':(font/16)+'rem'} as React.CSSProperties}>
  <div className="reading-toolbar"><label>גודל טקסט <select aria-label="גודל טקסט בקריאה" value={font} onChange={e=>{const n=Number(e.target.value);setFont(n);try{localStorage.setItem(FONT,String(n));}catch{/* local only */}}}>{[16,18,20,22].map(n=><option key={n} value={n}>{n}</option>)}</select></label>
   <label>מעבר לפרק <select aria-label="מעבר לפרק בקריאה" value={position} onChange={e=>go(e.target.value)}><option value="">בחירת פרק</option>{chapters.map(c=><option key={c.id} value={c.id}>{c.label}</option>)}</select></label>
   {savedChapter&&<button type="button" onClick={()=>go(savedChapter.id)}>המשך מהמקום ששמרתי</button>}
  </div>{children}<small>מקום הקריאה וגודל הטקסט נשמרים במכשיר הזה בלבד.</small>
 </div>;
 return <div className="reading-mode"><button type="button" className="primary" ref={trigger} onClick={()=>setOpen(true)}>מצב קריאה נקי</button>{open?<Modal title={title} close={()=>{setOpen(false);requestAnimationFrame(()=>trigger.current?.focus());}}>{content}</Modal>:content}</div>;
}
