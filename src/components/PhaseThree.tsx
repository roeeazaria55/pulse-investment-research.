import {WeeklyEarnings} from './MarketContext';
import type {Intelligence,DailyBriefing,Rating} from '../intelligenceTypes';
import type {News} from '../types';
import {Section,dateTime} from './UI';
const GITHUB='https://github.com/roeeazaria55/pulse-investment-research.';
export function WhyImportant({rating}:{rating:Rating}){
  return <details className="why-important"><summary>למה זה חשוב? • {rating.eventLabel}</summary>
    <p>{rating.why}</p><dl><dt>חשיבות האירוע למחקר</dt><dd>{rating.eventScore}/100 • אינה תחזית מחיר</dd><dt>אמינות המקור</dt><dd>{rating.sourceReliability}</dd><dt>רלוונטיות לחברה</dt><dd>{{direct:'שם חברה מפורש',context:'שם והקשר עסקי',rejected:'ההתאמה נפסלה'}[rating.companyRelevance]}</dd><dt>רמת ביטחון</dt><dd>{{high:'גבוהה במטא־נתון הראשוני',medium:'בינונית בשיוך, לא באמיתות הכתבה',low:'נמוכה'}[rating.confidence]}</dd><dt>בסיס המידע</dt><dd>{rating.basis==='headline-only'?'כותרת בלבד':'מטא־נתון רשמי שאומת'}</dd></dl>
    <small>כללים {rating.version} • העתקות של אותו דיווח אינן אישורים עצמאיים.</small>
  </details>;
}
export function DailyPanel({intel,date,news=[]}:{intel:Intelligence;date?:string;news?:News[]}){
  const b:DailyBriefing|undefined=intel.dailyBriefings.find(b=>b.date===date)||intel.dailyBriefings[0];
  if(!b)return <Section title="התדריך היומי"><p>טרם הופק תדריך לחלון שהסתיים ב־13:00.</p></Section>;
  return <Section title={`התדריך היומי • ${b.date}`} eyebrow="עברית • חלון קבוע עד 13:00">
    <div id={`briefing-${b.date}`} className="anchor-target"/>
    <p>חלון פרסום: {dateTime(b.startAt)} עד {dateTime(b.endAt)} • שעון ישראל</p>
    <p>הופק בפועל: {dateTime(b.generatedAt)}. ייתכנו עיכובים בריצות GitHub.</p>
    {!!b.revision&&<p>תיקון גרסה {b.revision} לאחר עדכון כללי חיפוש; מזהה התדריך והחלון נשמרו. הפקה ראשונה: {b.firstGeneratedAt?dateTime(b.firstGeneratedAt):'לא נמסר'}.</p>}
    <p className="alert">{b.notice}</p>
    <p>חיפושי חברות שהצליחו: {b.companySearchesSuccessful}/11 • חיפושי תעשייה: {b.industrySearchesSuccessful}/{intel.industries.config.industries.length}</p>
    {b.companies.map(c=><details className="daily-company" key={c.securityId}>
      <summary><b dir="auto">{c.name}</b> • {c.facts.length} אירועים בחלון</summary>
      {!c.facts.length&&<p>{c.searchStatus==='failed'?'החיפוש נכשל; אין להסיק שאין חדשות.':'לא נמצאו בחיפוש שהצליח כותרות מתוארכות בחלון זה.'}</p>}
      {c.facts.map(f=><article className="briefing-item" key={f.eventId}><p>{f.textHe}</p><a href={f.sourceUrl} target="_blank" rel="noopener noreferrer"><span dir="auto">{f.originalTitle}</span> ↗</a><p>{f.publisher} • {dateTime(f.publishedAt)} • קישור Google News כשמקורו בפיד RSS</p></article>)}
      <h3>הקשר ענפי</h3><p>{c.industryConnection}</p>
      <p>תחומי הקשר: {(intel.industries.config.companyIndustries[c.securityId]||[]).map(id=>intel.industries.config.industries.find(i=>i.id===id)?.name).filter(Boolean).join(' • ')}</p>
      {c.industryItemIds.map(id=>{const n=intel.industries.items.find(n=>n.id===id);return n?<article className="briefing-item" key={id}><a href={n.sourceUrl} target="_blank" rel="noopener noreferrer" dir="auto">{n.headline} ↗</a><p>{n.publisher} • {n.publishedAt?dateTime(n.publishedAt):'תאריך לא נמסר'} • כותרת בלבד, דרך Google News</p></article>:<p key={id}>הפריט הענפי יצא מחלון השימור.</p>;})}
      {!c.industryItemIds.length&&<p>לא נכללו כותרות ענף מתוארכות בחלון; מצב המקורות מפורט להלן.</p>}
      <h3>משמעות אפשרית למחקר — פרשנות</h3><p>{c.researchInterpretation}</p>
      <h3>מה חסר ומה לבדוק</h3><ul>{c.missing.map(t=><li key={t}>{t}</li>)}</ul>
      {c.undatedItemIds.length>0&&<details><summary>בנפרד: {c.undatedItemIds.length} פריטים ללא תאריך — מחוץ לחלון המאומת</summary>{c.undatedItemIds.map(id=>{const n=news.find(n=>n.id===id);return n?<a className="text-button" href={n.sourceUrl} key={id} target="_blank" rel="noopener noreferrer" dir="auto">{n.headline} ↗</a>:<p key={id}>פריט יצא מחלון השימור</p>;})}</details>}
    </details>)}
    <details><summary>מקורות תעשייה ומצב סיכום עברי</summary><p>{intel.summary.reason}</p><a className="text-button" href={intel.summary.proofRun} target="_blank" rel="noopener noreferrer">בדיקת היתכנות הסיכום</a>{intel.industries.sources.map(s=><p key={s.industryId}>{intel.industries.config.industries.find(i=>i.id===s.industryId)?.name} • {s.status==='results'?`${s.count} כותרות`:s.status==='zero-results'?'החיפוש הצליח ללא תוצאות':'כשל; נשמר מידע קודם'} • נבדק {dateTime(s.lastAttemptAt)}{s.error?` • ${s.error}`:''}</p>)}</details>
    {intel.industries.items.some(n=>!n.publishedAt)&&<details><summary>כותרות תעשייה ללא תאריך — אינן כלולות בחלון</summary>{intel.industries.items.filter(n=>!n.publishedAt).slice(0,10).map(n=><a className="text-button" href={n.sourceUrl} key={n.id} target="_blank" rel="noopener noreferrer" dir="auto">{n.headline} ↗</a>)}</details>}
    {intel.dailyBriefings.length>1&&<details><summary>תדריכים קודמים</summary>{intel.dailyBriefings.slice(1,8).map(b=><a className="text-button" href={`#briefing=${b.date}`} key={b.id}>{b.date}</a>)}</details>}
  </Section>;
}
export function CalendarPanel({intel,focus}:{intel:Intelligence;focus?:string}){return <WeeklyEarnings intel={intel} focus={focus}/>;}
export function NotificationsPanel({open=false}:{open?:boolean}){
  return <details className="panel notifications-panel" id="notification-setup" open={open||undefined}><summary>התראות לאנדרואיד • הגדרה חד־פעמית</summary>
    <p>אין עדיין הוכחה לקבלה בטלפון. אישור מהשרת אינו אישור מסירה.</p>
    <ol><li>התקינו ntfy לאנדרואיד ואשרו התראות. הגדירו בסוללה פעילות ברקע ללא הגבלה אם היצרן מגביל אותה.</li><li>צרו נושא אקראי ארוך. הירשמו אליו ב־ntfy בשרת ntfy.sh. ערוץ חינמי ללא בקרת גישה אינו פרטי מובטח.</li><li>ב־GitHub שמרו NTFY_TOPIC ו־PULSE_NOTIFY_CONFIG בתור Repository Secrets. פרטי הערוץ אינם מוזנים לאפליקציה או לצ׳אט.</li><li>פתחו את תהליך הניסיון, לחצו Run workflow, נעלו את הטלפון וסגרו את PULSE. ודאו שהתראה מגיעה ושהקשה פותחת את PULSE.</li></ol>
    <a className="primary text-button" href={`${GITHUB}/actions/workflows/notify-test.yml`} target="_blank" rel="noopener noreferrer">שליחת התראת ניסיון דרך Actions ↗</a>
    <p>הכפתור פותח ריצה מורשית ב־GitHub; נדרשת לחיצה על Run workflow. אין מפתח הרשאות בקוד הדפדפן.</p>
    <a className="text-button" href={`${GITHUB}/blob/main/docs/NOTIFICATIONS.md`} target="_blank" rel="noopener noreferrer">הגדרת שעות שקטות, השתקה, סוגים ותזכורות</a>
    <a className="text-button" href={`${GITHUB}/settings/secrets/actions`} target="_blank" rel="noopener noreferrer">פתיחת הגדרות Secrets ↗</a>
    <p>העדפות ההתראות ורשימת החברות שבמשימה נפרדות מהמעקב המקומי. שינוי במעקב אינו משנה התראות. נשלח רק מידע ציבורי, ללא תיק או הערות.</p>
  </details>;
}
