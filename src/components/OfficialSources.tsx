import {useEffect,useState} from 'react';
import {officialRegistry,officialCompany,officialTitle,parseOfficialSnapshot,type OfficialSnapshot} from '../data/official';
import {officialPack} from '../research/officialPack';
import {dateTime} from './UI';
const kinds={results:'פרסום תוצאות',schedule:'הודעה על מועד עתידי',document:'מסמך או מצגת',release:'הודעת חברה'};
const statuses={ok:'נאספו קישורים',failed:'הבדיקה האחרונה נכשלה', 'not-checked':'טרם נבדק'};
export function OfficialSources({ticker,name,onPrepare}:{ticker?:string;name?:string;onPrepare:(text:string)=>void}){
  const [active,setActive]=useState(officialCompany(ticker,name)?.id||'candidate-nebius');
  const [snapshot,setSnapshot]=useState<OfficialSnapshot|null>(null);
  const [error,setError]=useState('');const [loading,setLoading]=useState(true);const [reload,setReload]=useState(0);
  useEffect(()=>{const company=officialCompany(ticker,name);if(company)setActive(company.id);},[ticker,name]);
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);
    fetch(`${import.meta.env.BASE_URL}data/official-sources.json`,{cache:'no-cache',signal:controller.signal})
      .then(r=>{if(!r.ok)throw Error('Unavailable');return r.json();})
      .then(parseOfficialSnapshot).then(f=>{setSnapshot(f);setError('');})
      .catch(()=>{if(!controller.signal.aborted)setError('לא ניתן לקבל עדכון למקורות. פריטים קודמים, אם קיימים, נשארים מוצגים.');})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[reload]);
  const c=officialRegistry.companies.find(c=>c.id===active)!;
  const items=snapshot?.items.filter(n=>n.companyId===c.id)||[];
  return <section className="official-panel" aria-label="מקורות רשמיים וחבילת מחקר">
    <div className="official-heading"><div><small>מקורות החברה · כל 11 החברות</small><h2>מהמקור אל התזה.</h2></div><button onClick={()=>setReload(x=>x+1)} disabled={loading}>{loading?'בודק מקורות שמורים…':'רענון המקורות'}</button></div>
    <p>הודעות חברה, דוחות ומצגות — עם מקור ותאריך כאשר זמינים. תוכן המסמכים לא נאסף ולא סוכם ב־AI.</p>
    <div className="official-tabs" aria-label="חברה לחבילת מקורות">{officialRegistry.companies.map(x=><button key={x.id} aria-pressed={active===x.id} onClick={()=>setActive(x.id)}>{x.label}</button>)}</div>
    {error&&<p role="status">{error}</p>}
    <div className="official-statuses">{c.sources.map(source=>{const status=snapshot?.sources.find(s=>s.id===source.id);return <div key={source.id}>
      <a href={source.url} target="_blank" rel="noopener noreferrer">{source.label} ↗</a>
      <span>{status?statuses[status.status]:'מצב מקור לא זמין'}</span>
      {status?.lastAttemptAt&&<small>נבדק: {dateTime(status.lastAttemptAt)}</small>}
      {status?.lastSuccessfulAt&&<small>איסוף מוצלח אחרון: {dateTime(status.lastSuccessfulAt)}</small>}
      {status?.status==='failed'&&<small>ייתכן שקיים מידע חדש שלא נאסף. {status.error}</small>}
    </div>;})}</div>
    <div className="official-pack"><div><strong>חבילת מחקר ל־{c.label}</strong><p>מקורות ושאלות ממוקדות להעתקה ל־ChatGPT. הניתוח יתבצע לאחר פתיחת המקורות.</p></div><button className="primary" disabled={!snapshot||loading} onClick={()=>snapshot&&onPrepare(officialPack(active,snapshot))}>הכנת חבילת מקורות ל־{c.label}</button></div>
    {snapshot&&<small>מועד איסוף החבילה: {snapshot.generatedAt?dateTime(snapshot.generatedAt):'טרם בוצע איסוף'}. רענון כאן טוען את החבילה האחרונה; איסוף מאתרי החברות מתבצע בסריקה המתוזמנת.</small>}
    {!loading&&!items.length&&<p>טרם נאספו פריטים לחברה זו. הקישורים הרשמיים זמינים לבדיקה ידנית; אין להסיק שלא פורסם מידע.</p>}
    <div className="official-grid">{items.slice(0,8).map(n=><article key={n.id} className="official-card">
      <small>{kinds[n.kind]} · {n.metadataStatus==='page-metadata'?'כותרת נבדקה בעמוד המקור':'קישור מעמוד החברה'}</small>
      <h3><a href={n.url} target="_blank" rel="noopener noreferrer">{officialTitle(n)} ↗</a></h3>
      {n.language&&<small>שפה: {n.language==='he'?'עברית':'אנגלית'} · </small>}
      {n.titleBasis==='filename'&&<small>השם מבוסס על שם הקובץ · </small>}
      {n.documentPeriod&&<p>{n.periodBasis==='filename-hint'?'רמז לתקופה בשם הקובץ — טעון בדיקה':'תקופה המופיעה בכותרת'}: {n.documentPeriod}</p>}
      <p>פורסם: {n.publishedDate||'תאריך לא זמין במטא־נתונים'}</p>
      <small>נאסף לראשונה: {dateTime(n.collectedAt)}<br/>נראה לאחרונה במקור: {dateTime(n.lastSeenAt)}</small>
      {n.metadataError&&<p className="muted">בדיקת עמוד המסמך לא הושלמה. יש לפתוח את המקור.</p>}
      <details><summary>מה אומת ומה חסר?</summary><p>הקישור נמצא בעמוד החברה. {n.metadataStatus==='page-metadata'?'כותרת העמוד נקראה.':'כותרת הקישור בלבד נאספה.'} תוכן המסמך והנתונים הכספיים לא נותחו. אין להסיק תאריך פרסום מתקופת דוח, משם קובץ או ממועד האיסוף.</p>{n.publishedDate&&n.dateEvidenceUrl&&<a href={n.dateEvidenceUrl} target="_blank" rel="noopener noreferrer">מקור לתאריך הפרסום ({n.publishedDateBasis==='index-time'?'תאריך בכרטיס הפרסום':'מטא־נתונים של המקור'}) ↗</a>}{n.metadataCheckedAt&&<small>בדיקת מטא־נתונים אחרונה: {dateTime(n.metadataCheckedAt)}</small>}</details>
    </article>)}</div>
  </section>;
}
