import {useReportIntake} from '../hooks/useReportIntake';
import {financialMappingReadiness} from '../research/financialMappingReadiness';
import {ResearchTableView} from './SuppliedResearch';
const statuses={ok:'הקריאה האחרונה הושלמה',partial:'הקריאה הושלמה חלקית',failed:'הקריאה האחרונה נכשלה',deferred:'ממתין לסבב איסוף נוסף','no-candidates':'לא נמצא קישור מתאים במאגר הנוכחי'};
export function ReportIntake({companyId}:{companyId:string}){
 const {data,failed}=useReportIntake(companyId);
 const source=data?.sources.find(s=>s.companyId===companyId),docs=data?.documents.filter(d=>d.companyId===companyId)||[];
 const readiness=financialMappingReadiness(data,companyId);
 if(data&&!source&&!docs.length&&!readiness)return null;
 return <details className="report-intake" aria-label="קליטת תוכן דוחות רשמיים"><summary>קליטת דוחות אוטומטית{docs.length?` · ${docs.length} מסמכים נקראו`:''}</summary>
  <p>המערכת קוראת תוכן ממקורות רשמיים ומחלצת טבלאות ונתונים מובנים כשהם זמינים. הנתונים ממתינים לבדיקת תקופה והגדרה; המחקר ומחיר השווי אינם משתנים אוטומטית.</p>
  {readiness&&<div aria-label={`פערי כיסוי פיננסי של ${readiness.ticker}`}>
   <p><strong>כיסוי פיננסי · {readiness.ticker} · ממתין לאימות</strong></p>
   {data&&<p>{readiness.documents.length} מסמכי מקור · {readiness.structuredFacts} עובדות מובנות לפני בדיקת התאמה · {readiness.semanticMappings} מיפויים חשבונאיים. ספירת עובדות אינה אישור להשוואה.</p>}
   <ul>{readiness.gaps.map(gap=><li key={gap.code}>{gap.label}</li>)}</ul>
   <p><b>מה חסר לפני מיפוי והשוואה:</b></p>
   <ul>{readiness.requirements.map(requirement=><li key={requirement}>{requirement}</li>)}</ul>
  </div>}
  {failed?<p role="status">מצב הקליטה אינו זמין. אין להסיק מכך שלא פורסם דוח.</p>:!data?<p role="status">טוען מצב קליטה…</p>:<>
   {source&&<p>{statuses[source.status]} · ניסיון אחרון {new Date(source.lastAttemptAt).toLocaleString('he-IL')}. {source.status!=='ok'&&'ייתכן שקיימים דיווחים נוספים שלא נקלטו.'}</p>}
   {!docs.length&&<p>אין עדיין תוכן דוח שנקרא בהצלחה במאגר הזה. קישורי הדיווחים זמינים במקורות; כשל קריאה אינו היעדר דיווח.</p>}
   {docs.map(d=><details className="intake-document" key={d.id}><summary>{d.title}{d.revised?' · זוהתה גרסה מתוקנת':''}</summary>
    <p><a href={d.finalUrl} target="_blank" rel="noopener noreferrer">פתיחת הדיווח הרשמי ↗</a></p>
    <p>תאריך פרסום: {d.publishedDate||'לא אומת'} · תקופה לפי מטא־נתונים: {d.documentPeriod||'לא נקבעה'}; יש לאמת מול כותרות הטבלאות.</p>
    <p>נקרא בהצלחה: {new Date(d.lastSuccessfulAt).toLocaleString('he-IL')} · {d.format.toUpperCase()} · {d.readScope==='full-body'?'כל גוף המסמך':'קריאה חלקית בלבד'}{d.pages?` · ${d.pages} עמודים במסמך`:''}.</p>
    {d.error&&<p role="status">העדכון האחרון נכשל; מוצגת הקריאה הקודמת שהצליחה.</p>}
    <p>{d.facts.length} נתוני XBRL מובנים · {d.tableCount} טבלאות זוהו{d.tablesTruncated?' · מוצגות עד 12 טבלאות':''}. חילוץ אינו אימות חשבונאי.</p>
    {!!d.facts.length&&<details><summary>נתונים מובנים לפי תקופה ויחידה</summary><ResearchTableView table={{type:'table',columns:['תג מקור','ערך ביחידת המקור','יחידה','מתאריך','עד / בתאריך'],rows:d.facts.map(f=>[f.concept,f.value.toLocaleString('en-US',{maximumFractionDigits:8}),f.unit,f.start||'נתון מאזני',f.end])}}/></details>}
    {!!d.tables.length&&<details><summary>שורות מטבלאות המקור · לבדיקת תקופה ויחידות</summary><p>שורות נבחרות בלבד. אין להסיק תקופה ממיקום עמודה, ואין להשוות בין GAAP, מדדים מתואמים ותחזיות ללא גישור.</p>{d.tables.map((t,i)=>{const width=Math.max(1,...t.rows.map(row=>row.length));return <div key={i}><p>טבלה {i+1}{t.page?` · עמוד ${t.page}`:''}{t.spans?' · במקור תאים ממוזגים':''}</p><ResearchTableView table={{type:'table',columns:Array.from({length:width},(_,j)=>`עמודת מקור ${j+1}`),rows:t.rows.map(row=>Array.from({length:width},(_,j)=>row[j]||''))}}/></div>;})}</details>}
    <small>גרסאות קודמות שזוהו: {d.revisions.length} · SHA-256: <bdi>{d.sha256}</bdi></small>
   </details>)}
  </>}
 </details>;
}

