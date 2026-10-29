import {useEffect,useState} from 'react';
import {ShieldCheck,Wallet,Sun,Moon,BrainCircuit,Database,AlertTriangle} from 'lucide-react';

type Receipt={id:string;model:string;usd:string;calledAt:string};
type Hold={id:string;maxUsd:string;heldAt:string};
type CostLedger={version:number;calls:Receipt[];holds:Hold[]};
function positive(v:string):number|null{
 const n=Number(v);
 return Number.isFinite(n)&&n>=0&&n<=10000?n:null;
}
export function summarizeCosts(value:unknown,now=new Date()){
 if(!value||typeof value!=='object')throw Error('Cost ledger malformed');
 const v=value as CostLedger;
 if(v.version!==1||!Array.isArray(v.calls)||!Array.isArray(v.holds)||v.calls.length>10000||v.holds.length>10000)
  throw Error('Cost ledger malformed');
 const month=now.toISOString().slice(0,7);
 let spent=0,reserved=0;
 const ids=new Set<string>();
 for(const c of v.calls){
  if(!c||!/^([a-f0-9]{64})$/.test(c.id)||ids.has(c.id)||!Number.isFinite(Date.parse(c.calledAt)))
   throw Error('Cost receipt unverified');
  ids.add(c.id);
  if(c.calledAt.slice(0,7)===month){
   const n=positive(c.usd);if(n===null)throw Error('Bad receipt amount');spent+=n;
  }
 }
 for(const h of v.holds){
  if(!h||!/^([a-f0-9]{64})$/.test(h.id)||ids.has(h.id)||!Number.isFinite(Date.parse(h.heldAt)))
   throw Error('Cost reservation unverified');
  ids.add(h.id);
  if(h.heldAt.slice(0,7)===month){
   const n=positive(h.maxUsd);if(n===null)throw Error('Bad hold amount');reserved+=n;
  }
 }
 return {spent,reserved,remaining:Math.max(0,9-spent-reserved),month};
}
export function AISettingsPanel({theme,onThemeChange}:{theme:'dark'|'light';onThemeChange:(v:'dark'|'light')=>void}){
 const [usage,setUsage]=useState<ReturnType<typeof summarizeCosts>|null>(null);
 const [status,setStatus]=useState<'loading'|'unavailable'|'available'>('loading');
 useEffect(()=>{
  let active=true;
  fetch(import.meta.env.BASE_URL+'data/ai-cost-ledger.json',{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Cost state not published');return summarizeCosts(await r.json());})
   .then(v=>{if(active){setUsage(v);setStatus('available');}})
   .catch(()=>{if(active)setStatus('unavailable');});
  return ()=>{active=false;};
 },[]);
 return <div className="pulse-ai-settings" dir="rtl">
  <section>
   <h3><Sun size={17}/> תצוגה</h3>
   <p>בחר את סגנון התצוגה. השינוי נשמר בדפדפן שלך בלבד.</p>
   <div className="pulse-appearance-switch" role="group" aria-label="מצב תצוגה">
    <button aria-pressed={theme==='dark'} className={theme==='dark'?'selected':''}
      onClick={()=>onThemeChange('dark')}><Moon size={16}/> כהה</button>
    <button aria-pressed={theme==='light'} className={theme==='light'?'selected':''}
      onClick={()=>onThemeChange('light')}><Sun size={16}/> בהיר</button>
   </div>
  </section>
  <section>
   <h3><BrainCircuit size={18}/> מנוע המחקר</h3>
   <p>הפעלת AI בתשלום דורשת מפתח חסוי והרשאה מפורשת מצד בעל המאגר, דרך GitHub Actions. אי אפשר להפעיל חיוב מהדפדפן.</p>
   <div className="pulse-ai-settings-status"><ShieldCheck size={16}/> סטטוס: אין אימות הפעלה דרך האתר הציבורי</div>
  </section>
  <section>
   <h3><Wallet size={17}/> תקציב מתוכנן — $10 לחודש פעיל</h3>
   <p>הזמנה מקומית עד $9 והשארת $1 כרזרבה. ספק ה־API הוא מקור האמת לחיוב.</p>
   {status==='loading'&&<p role="status">בודק נתוני שימוש…</p>}
   {status==='unavailable'&&<p role="status"><AlertTriangle size={15}/> נתוני שימוש טרם פורסמו. אין להסיק שההוצאה הייתה $0.</p>}
   {usage&&<div className="pulse-ai-usage">
    <div><span>שימוש שנרשם</span><strong><bdi>${usage.spent.toFixed(2)}</bdi></strong></div>
    <div><span>תקציב משוריין</span><strong><bdi>${usage.reserved.toFixed(2)}</bdi></strong></div>
    <div><span>נותר להפעלות חדשות עד $9</span><strong><bdi>${usage.remaining.toFixed(2)}</bdi></strong></div>
    <small>תקופה: <bdi>{usage.month}</bdi> UTC · הנתונים הם אומדן מקומי, לא חשבונית מאומתת</small>
   </div>}
  </section>
  <section>
   <h3><Database size={17}/> פרטיות ונתונים</h3>
   <p>האחזקות והערות המחקר האישיות נשמרות בדפדפן; קובצי המחקר הציבוריים אינם בעלי גישה אליהן. מחקר AI לא יחליף מודל מאושר ללא אישור GitHub מאומת.</p>
  </section>
 </div>;
}
