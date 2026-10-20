import type {IntakeDocument,ReportIntakeSnapshot} from '../data/reportIntake';
import type {MetricPoint,ThesisMetric} from './thesisMonitoring';
interface Mapping {companyId:string;metricId:string;concepts:string[];basis:string;divisor:number;unit:string;fiscalJune?:boolean}
// Explicit semantic mappings only. No inferred PDF columns, company extensions, adjusted or normalized measures.
const mappings:Mapping[]=[
 {companyId:'us-smci-nasdaq-common',metricId:'revenue',concepts:['us-gaap:revenues','us-gaap:revenuefromcontractwithcustomerexcludingassessedtax'],basis:'revenue',divisor:1e9,unit:'USD billion',fiscalJune:true},
 {companyId:'us-smci-nasdaq-common',metricId:'cashflow',concepts:['us-gaap:netcashprovidedbyusedinoperatingactivities'],basis:'operating cash flow',divisor:1e9,unit:'USD billion',fiscalJune:true},
 {companyId:'candidate-brainsway',metricId:'revenue',concepts:['us-gaap:revenues','us-gaap:revenuefromcontractwithcustomerexcludingassessedtax'],basis:'revenue',divisor:1e6,unit:'USD million'},
 {companyId:'candidate-brainsway',metricId:'profit',concepts:['us-gaap:operatingincomeloss'],basis:'operating income',divisor:1e6,unit:'USD million'},
];
/** Only exact calendar boundaries are recognized. Fiscal 52/53-week calendars require a separate mapping. */
function period(start:string|null,end:string,fiscalJune=false):string|null{
 if(!start)return null;
 const year=Number(end.slice(0,4));
 if(fiscalJune)return start===`${year-1}-07-01`&&end===`${year}-06-30`?`FY${year}`:null;
 if(start===`${year}-01-01`&&end===`${year}-12-31`)return String(year);
 const quarters=[['01-01','03-31'],['04-01','06-30'],['07-01','09-30'],['10-01','12-31']];
 const q=quarters.findIndex(([a,b])=>start===`${year}-${a}`&&end===`${year}-${b}`);
 return q<0?null:`Q${q+1} ${year}`;
}
export interface SourceObservation {point:MetricPoint;document:IntakeDocument;concept:string;context:string;start:string;end:string}
export interface ReportComparison {status:'mapped'|'missing'|'unsupported'|'conflict'|'review';label:string;observation?:SourceObservation}
export function reportComparison(data:ReportIntakeSnapshot,companyId:string,metric:ThesisMetric):ReportComparison{
 const rules=mappings.filter(m=>m.companyId===companyId&&m.metricId===metric.id);
 if(!rules.length)return {status:'unsupported',label:'נדרשת בדיקת טבלה או הגדרה לפני מיפוי אוטומטי'};
 const candidates:SourceObservation[]=[];
 for(const document of data.documents.filter(d=>d.companyId===companyId))for(const rule of rules)for(const fact of document.facts){
  if(!rule.concepts.includes(fact.concept.toLowerCase())||fact.unit!=='iso4217:USD'||!Number.isFinite(fact.value))continue;
  const label=period(fact.start,fact.end,rule.fiscalJune);if(!label)continue;
  candidates.push({point:{value:fact.value/rule.divisor,period:label,unit:rule.unit,basis:rule.basis},document,concept:fact.concept,context:fact.context,start:fact.start!,end:fact.end});
 }
 if(!candidates.length)return {status:'missing',label:'טרם נקלט נתון מובנה עם תקופה ויחידה מתאימות'};
 // Prefer the forecast period, then the latest actual period; never replace it with a publication date.
 const samePeriod=candidates.filter(c=>c.point.period===metric.target?.period);
 const pool=samePeriod.length?samePeriod:candidates;
 const latestEnd=pool.map(c=>c.end).sort().at(-1)!;
 const selected=pool.filter(c=>c.end===latestEnd);
 if(selected.some(c=>c.document.revised||c.document.error))return {status:'review',label:'דוח מתוקן או עדכון שנכשל · נדרשת בדיקה לפני השוואה'};
 if(new Set(selected.map(c=>JSON.stringify(c.point))).size!==1)return {status:'conflict',label:'נתוני מקור סותרים · אין השוואה עד לבירור'};
 selected.sort((a,b)=>b.document.lastSuccessfulAt.localeCompare(a.document.lastSuccessfulAt));
 return {status:'mapped',label:'מיפוי אוטומטי מנתון מקור · ממתין לאימות',observation:selected[0]};
}
