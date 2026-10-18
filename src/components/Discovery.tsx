import registry from '../../public/data/news-registry.json';
import type { LiveFeed } from '../types';
import { dateTime, Section } from './UI';
const norm = (v:string) => v.toLowerCase().replace(/[^a-z0-9\u0590-\u05ff]/g,'');
export function WebNewsSearch({name}:{name:string}) {
  const c=registry.companies.find(c=>[c.name,...c.aliases].some(a=>norm(a)===norm(name)));
  const q=c?.query || `"${name.replaceAll('"','')}" company news`;
  return <a className="text-button" href={`https://www.google.com/search?tbm=nws&q=${encodeURIComponent(q)}`} target="_blank" rel="noopener noreferrer">חיפוש חדשות ברשת ↗</a>;
}
export function DiscoveryPanel({feed}:{feed:LiveFeed}) {
  const d=feed.discovery;
  if(!d) return null;
  const ok=d.sources.filter(s=>s.status!=='failed');
  const withResults=d.sources.filter(s=>s.status==='results');
  const briefing=d.briefings[0];
  return <Section title="חדשות חברות מהרשת" eyebrow="כותרות ומטא־נתונים • ללא ניתוח AI">
    <p>{withResults.length} חברות עם תוצאות • {ok.length-withResults.length} ללא תוצאות • {d.sources.length-ok.length} נכשלו.</p>
    <p>בדיקה אחרונה: {dateTime(d.lastAttemptAt)} • הצלחת חיפוש מלאה: {d.lastSuccessfulAt?dateTime(d.lastSuccessfulAt):'טרם הושגה'}</p>
    <p>חלון חיפוש: 30 יום. לא נקראו כתבות מלאות. כותרת עשויה לכלול דעה או תחזית של המפרסם.</p>
    {d.noNewItems && <p className="alert">אין פריטים חדשים בחיפושים שהצליחו. פריטים קודמים נשמרים.</p>}
    {d.status!=='complete' && <p className="alert">כיסוי {d.status==='failed'?'נכשל':'חלקי'}: מידע קודם נשמר עם התאריכים המקוריים.</p>}
    <details><summary>סטטוס ספקים וחיפושים לכל חברה</summary>
      {d.registry.providers.map(p=><p key={p.id}><b dir="ltr">{p.id}</b> • {p.enabled?'פעיל לחיפוש':'מושבת'} • {p.enabled?`${d.sources.filter(s=>s.provider===p.id&&s.status!=='failed').length}/${d.sources.filter(s=>s.provider===p.id).length} חיפושים הצליחו`:'בדיקת Actions נכשלה: HTTP 429'} • נבדק: {p.enabled?dateTime(d.lastAttemptAt):p.proofCheckedAt?dateTime(p.proofCheckedAt):'ראו ריצת בדיקה'} <a href={p.proofRun} target="_blank" rel="noopener noreferrer">הוכחת בדיקה</a></p>)}
      {d.sources.map(s=><article className="source-status" key={s.provider+s.securityId}>
        <h3>{s.name}</h3><p>{s.provider} • {s.status==='results'?`${s.count} כותרות רלוונטיות`:s.status==='zero-results'?'החיפוש הצליח — אפס תוצאות':'החיפוש נכשל'}</p>
        <p>ניסיון: {dateTime(s.lastAttemptAt)} • הצלחה: {s.lastSuccessfulAt?dateTime(s.lastSuccessfulAt):'אין'} • נפסלו: {s.rejectedCount}</p>
        {s.error&&<p>{s.error}</p>}
        <p>אימות זהות לחיפוש בלבד: {d.registry.companies.find(c=>c.id===s.securityId)?.identityVerification.date}</p>
        <WebNewsSearch name={s.name}/>
      </article>)}
    </details>
    {briefing&&<details><summary>תדריך {briefing.id.endsWith('morning')?'בוקר':'ערב'} — תבנית כותרות</summary>
      <p>{briefing.id.split(':')[0]} • Asia/Jerusalem • {dateTime(briefing.generatedAt)}</p>
      <p>כותרות חדשות שנמצאו בתקופה זו, לרבות אתחול של 30 יום; אין זו שעת התרחשות האירועים.</p>
      {briefing.itemIds.slice(0,15).map(id=>{const n=feed.news.find(n=>n.id===id);return n?<article className="briefing-item" key={id}><a href={n.sourceUrl} target="_blank" rel="noopener noreferrer">{n.headline}</a><p>{n.sourceName} • {n.publishedAt?dateTime(n.publishedAt):'תאריך פרסום לא נמסר'}</p><p>{n.classification?.reason}</p></article>:null;})}
      <ul>{briefing.questions.map(q=><li key={q}>{q}</li>)}</ul>
    </details>}
  </Section>;
}
