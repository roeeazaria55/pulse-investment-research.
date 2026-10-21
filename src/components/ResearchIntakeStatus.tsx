import intake from '../data/researchIntakeRegistry.json';
import sources from '../data/newResearchSourceManifest.json';
import {hasFullResearch} from './FullCompanyResearch';

export function ResearchIntakeStatus({companyId}:{companyId:string}){
 const item=intake.companies.find(r=>r.companyId===companyId);
 if(!item)return null;
 const file=sources.research.find(r=>r.companyId===companyId);
 const active=hasFullResearch(companyId);
 return <details className="research-import-info" data-testid="research-intake-status">
  <summary>סטטוס קליטת המחקר המלא</summary>
  <p><strong>{active?'מחקר מלא זמין לקריאה באתר':'המחקר החדש טרם נקלט במלואו באתר'}</strong></p>
  <p>קובץ מקור מיועד: <span dir="ltr">{item.filename}</span></p>
  <p>שלב קליטה: {item.status==='existing-source-recheck'?'מקור קודם במאגר — ממתין לבדיקה חוזרת':'קובץ חדש בחבילת ייבוא חיצונית — טרם נשמר במאגר'}</p>
  {file&&<p>זיהוי קובץ שהועלה: {file.pages} עמודים · SHA-256 <code dir="ltr">{file.sha256}</code>. הזיהוי אינו אימות של הנתונים הפיננסיים בדוח.</p>}
  <p>מעקב ייעודי מתוכנן: {item.priorityMonitor}</p>
  <p>הנתונים שהועלו הם מחקר עצמאי. אין לסמן אותם כנתוני חברה מאומתים או כתחזית מאושרת ללא בקרת מקורות ומודל.</p>
 </details>;
}
