import type {ReportIntakeSnapshot} from '../data/reportIntake';
import {metricsWithSemanticMapping} from './financialMetricMappings';

/** Review requirements, not executable mappings or a claim of issuer verification. */
export const pilotFinancialRequirements = [
 {companyId:'candidate-nebius',ticker:'NBIS',requirements:[
  'הכנסות: קבוצה מאוחדת בנפרד מ־AI Cloud, ARR וצבר; תקופות קלנדריות מדויקות.',
  'רווח תפעולי בנפרד מ־Adjusted EBITDA ומרווח מתואם; נדרש גישור להגדרת התחזית.',
  'תזרים תפעולי ו־CAPEX: תקופה מצטברת מפורשת, מקדמות לקוחות ורכוש קבוע מול נכסים בלתי מוחשיים; אין חיסור YTD אוטומטי.',
  'מזומן וחוב: יתרות באותו תאריך, מזומן מוגבל ומקדמות בנפרד; מסגרת אשראי אינה חוב שנמשך.',
  'מניות מדוללות: ממוצע משוקלל לתקופה מול יתרה בתאריך והנחת דילול עתידית.',
 ]},
 {companyId:'candidate-iren',ticker:'IREN',requirements:[
  'הכנסות: הכנסה מאוחדת בנפרד מהכנסות AI, כרייה ו־ARR; שנת כספים המסתיימת ביוני אינה שנה קלנדרית.',
  'רווח תפעולי בנפרד מ־EBITDA מתואם וירידות ערך; נדרשת הגדרה חשבונאית מהדוח.',
  'תזרים תפעולי ו־CAPEX: תקופת רבעון מול YTD, מזומן ששולם מול התחייבויות ומקדמות; אין להסיק תזרים ממימון GPU.',
  'מזומן וחוב: תאריך יתרה אחיד, מגבלות שימוש, הלוואות ומסגרות שטרם נמשכו בנפרד.',
  'מניות מדוללות: ממוצע משוקלל, המרות וכתבי אופציה; הנחת מודל אינה מספר מניות מדווח.',
 ]},
 {companyId:'us-dlo-nasdaq-a',ticker:'DLO',requirements:[
  'הכנסות ורווח גולמי: הגדרות IFRS מהדוח; TPV ו־GP/TPV אינם הכנסות או שיעור רווח גולמי רגיל.',
  'רווח תפעולי והוצאות תפעול: היקף סעיפים והתאמות מפורשים; אין למפות תג US GAAP לפי דמיון בשם.',
  'תזרים תפעולי ו־CAPEX: תקופה ויחידה מפורשות; Adjusted FCF אינו תזרים IFRS ואין להחליף ביניהם.',
  'מזומן וחוב: מזומן תאגידי בנפרד מכספי סוחרים ומיתרות מוגבלות, באותו תאריך.',
  'מניות מדוללות: ממוצע לתקופה, סוגי מניות ורכישות חוזרות; 295M במודל אינו נתון מדווח מאומת.',
 ]},
] as const;

export type FinancialReadinessGap = {
 code:'snapshot-unavailable'|'intake-not-observed'|'source-incomplete'|'reports-missing'|'structured-facts-missing'|'mapping-review-required'|'document-review-required';
 label:string;
};

/** Call with a validated snapshot. Table cells and research/model values never count as facts. */
export function financialMappingReadiness(data:ReportIntakeSnapshot|null,companyId:string){
 const pilot=pilotFinancialRequirements.find(p=>p.companyId===companyId);
 if(!pilot)return undefined;
 const documents=data?.documents.filter(d=>d.companyId===companyId)??[];
 const source=data?.sources.find(s=>s.companyId===companyId);
 const structuredFacts=documents.reduce((sum,d)=>sum+d.facts.length,0);
 const semanticMappings=metricsWithSemanticMapping(companyId).size;
 const gaps:FinancialReadinessGap[]=[];
 if(!data)gaps.push({code:'snapshot-unavailable',label:'מצב קליטת הדוחות אינו זמין; לא ניתן לקבוע כיסוי נתונים.'});
 else {
  if(!source)gaps.push({code:'intake-not-observed',label:'אין רישום קליטת דוחות לחברה בתמונת הנתונים הנוכחית.'});
  else if(source.status!=='ok')gaps.push({code:'source-incomplete',label:'האיסוף האחרון לא הושלם בהצלחה; ייתכן שקיימים דיווחים שלא נקלטו.'});
  if(!documents.length)gaps.push({code:'reports-missing',label:'טרם נקלט תוכן דוח רשמי לחברה במאגר הזה.'});
  else if(!structuredFacts)gaps.push({code:'structured-facts-missing',label:'הדוחות שנקראו אינם כוללים עובדות מובנות נתמכות; טבלאות וטקסט דורשים מתאם מקור ובדיקת כותרות, תקופות ויחידות.'});
  if(documents.some(d=>d.revised||d.error))gaps.push({code:'document-review-required',label:'קיימת גרסה מתוקנת או קריאה שנכשלה; נדרשת בדיקת המקור לפני השוואה.'});
 }
 if(!semanticMappings)gaps.push({code:'mapping-review-required',label:'אין מיפוי חשבונאי מאושר לחברה; נדרשת התאמת חברה, היקף איחוד, תקופה, יחידה והגדרה.'});
 return {companyId,ticker:pilot.ticker,requirements:pilot.requirements,documents,source,structuredFacts,semanticMappings,gaps};
}
