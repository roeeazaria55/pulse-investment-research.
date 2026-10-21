import intake from '../data/researchIntakeRegistry.json';
import sources from '../data/newResearchSourceManifest.json';
import candidates from '../data/newResearchScenarioCandidates.json';
import {auditSourceValuation} from '../research/sourceValuationAudit';
import {hasFullResearch} from './FullCompanyResearch';
import {UnverifiedFullResearch} from './UnverifiedFullResearch';

export function ResearchIntakeStatus({companyId}:{companyId:string}){
 const item=intake.companies.find(r=>r.companyId===companyId);
 if(!item)return null;
 const file=sources.research.find(r=>r.companyId===companyId);
 const active=hasFullResearch(companyId);
 const candidate=candidates.companies.find(c=>c.companyId===companyId);
 const audit=candidate?auditSourceValuation(candidate.scenarios.map(s=>({id:s.id as 'bear'|'base'|'bull',weight:s.weight,price:s.price})),candidate.declared,candidate.tolerance):null;
 return <details className="research-import-info" data-testid="research-intake-status">
  <summary>סטטוס קליטת המחקר המלא</summary>
  <p><strong>{active?'מחקר מלא זמין לקריאה באתר':'המחקר החדש טרם נקלט במלואו באתר'}</strong></p>
  <p>קובץ מקור מיועד: <span dir="ltr">{item.filename}</span></p>
  <p>שלב קליטה: {item.status==='existing-source-recheck'?'מקור קודם במאגר — ממתין לבדיקה חוזרת':'מסמך מקור וטקסט עמודים נשמרו במאגר — תוכן פיננסי ממתין לאימות'}</p>
  {file&&<p>פרטי קובץ מקור שמור במאגר: {file.pages} עמודים · SHA-256 <code dir="ltr">{file.sha256}</code>. הזיהוי אינו אימות של הנתונים הפיננסיים בדוח.</p>}
  <p>מעקב ייעודי מתוכנן: {item.priorityMonitor}</p>
  {candidate&&<details><summary>תרחישי מחקר מועמדים — לא מאושרים</summary>
   <p>מחקר מתאריך {candidate.asOf} · מטבע {candidate.currency} · אופק שווי {candidate.horizon} · מחיר ייחוס היסטורי {candidate.reference}</p>
   <p>סוג הבסיס: {candidate.basis}</p>
   <ul>{candidate.scenarios.map(s=><li key={s.id}>{s.id}: {s.weight}% · {s.price} {candidate.currency}</li>)}</ul>
   <p role={audit?.status==='discrepancy'?'alert':undefined}>שווי מחושב: {audit?.calculated?.toFixed(3)} · שווי שהופיע במסמך: {candidate.declared} · {audit?.status==='discrepancy'?'קיים פער המחייב בירור':'חושב עם סבילות העיגול של המקור'}</p>
   <p>בדיקות חסרות:</p><ul>{candidate.flags.map(flag=><li key={flag}>{flag}</li>)}</ul>
   <p>לא אומת מול דוחות החברה. השווי הפעיל לא משתנה.</p>
  </details>}
  {file&&<UnverifiedFullResearch companyId={companyId}/>}
  <p>הנתונים המוצגים הם רישום מחקר עצמאי ולא אישור לקליטת הקובץ המקורי. אין לסמן אותם כנתוני חברה מאומתים או כתחזית מאושרת ללא בקרת מקורות ומודל.</p>
 </details>;
}
