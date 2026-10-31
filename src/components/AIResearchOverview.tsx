import {useEffect,useState} from 'react';
import {BrainCircuit,ArrowUpLeft,FileClock,ShieldCheck,Wallet} from 'lucide-react';
import registry from '../../public/data/official-registry.json';
import {validateCandidateStore} from './EarningsResearchCandidates';

type Stats={drafts:number;companies:number;needsReview:number;blocked:number};
export function AIResearchOverview({onOpenResearch}:{onOpenResearch:()=>void}){
 const [stats,setStats]=useState<Stats|null>(null);
 const [unavailable,setUnavailable]=useState(false);
 useEffect(()=>{
  let active=true;
  fetch(import.meta.env.BASE_URL+'data/earnings-research-candidates.json',{cache:'no-store'})
   .then(async res=>{if(!res.ok)throw Error('Drafts not published');return res.json();})
   .then(data=>{
    const rows=registry.companies.flatMap(company=>validateCandidateStore(data,company.id));
    if(active)setStats({drafts:rows.length,
      companies:new Set(rows.map(x=>x.companyId)).size,
      needsReview:rows.filter(x=>x.status==='needs-review').length,
      blocked:rows.filter(x=>x.status==='blocked').length});
   })
   .catch(()=>{if(active)setUnavailable(true);});
  return ()=>{active=false;};
 },[]);
 return <section className="pulse-ai-command" dir="rtl" aria-label="מצב מחקר PULSE AI">
  <div className="pulse-ai-command-head">
   <div className="pulse-ai-mark" aria-hidden="true"><BrainCircuit size={23}/></div>
   <div>
    <span className="pulse-ai-kicker">PULSE INTELLIGENCE / RESEARCH ENGINE</span>
    <h2>המחקר שלך, צעד אחד לפני השוק.</h2>
   </div>
   <span className="pulse-ai-pill"><ShieldCheck size={14}/> בקרת אנליסט</span>
  </div>
  <p className="pulse-ai-command-description">מעקב דוחות, אימות מקורות והכנת טיוטות השקעה. הפעלת ניתוח AI מנוהלת ב־GitHub לפי הרשאות ותקציב; מסך זה אינו מאמת אם האוטומציה פעילה.</p>
  <div className="pulse-ai-kpis">
   <div><span><FileClock size={16}/> טיוטות מקור שמורות</span><strong>{stats?stats.drafts.toLocaleString('he-IL'):'—'}</strong><small>{stats?stats.companies+' חברות עם טיוטות':'ממתין לנתוני המקורות'}</small></div>
   <div><span><ShieldCheck size={16}/> ממתינות לבדיקה</span><strong>{stats?stats.needsReview.toLocaleString('he-IL'):'—'}</strong><small>{stats?stats.blocked+' חסומות עקב מקור/נתון':'אין סטטוס מאומת'}</small></div>
   <div><span><Wallet size={16}/> יעד תקציב AI</span><strong><bdi>$10</bdi></strong><small>לחודש פעיל · לא חיוב קבוע</small></div>
  </div>
  {unavailable&&<p className="pulse-ai-unavailable" role="status">נתוני טיוטות טרם פורסמו בענף זה. המחקר הקודם אינו מושפע.</p>}
  <div className="pulse-ai-command-bottom">
   <span><span className="pulse-ai-live-dot" aria-hidden="true"/> איסוף מקורות נפרד מהפעלת מודל בתשלום</span>
   <button type="button" className="pulse-ai-link" onClick={onOpenResearch}>מעבר למחקר החברות <ArrowUpLeft size={17}/></button>
  </div>
 </section>;
}
