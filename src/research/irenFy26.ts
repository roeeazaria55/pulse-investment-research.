import source from '../../public/data/iren-fy26-source.json';
import model from '../data/models/iren.json';
import {metricComparison,type MetricPoint} from './thesisMonitoring';
import {validDate} from './exchange';

export type IrenMetricId='revenue'|'cashflow'|'capex';
export interface IrenObservation {
 id:IrenMetricId;title:string;point:MetricPoint;periodEnd:'2026-06-30';periodText:string;
 definition:string;sourceValues:{label:string;raw:string;value:number}[];
 sourceUrl:string;pdfUrl:string;pdfPage:number;checkedDate:string;publishedDate:string;
 verification:'source-checked-pending-review'|'derived-source-checked-pending-review';
}
export interface IrenForecast {point:MetricPoint;description:string;definition:string;asOf:string}
type Table={statement:string;unit:string;periodKind:string;periodEnd:string;pdfPage:number;rows:{label:string;current:string}[]};
type Source={version:number;companyId:string;title:string;sourceUrl:string;pdfUrl:string;checkedDate:string;publishedDate:string;reviewStatus:string;tables:Table[]};
const sourceUrl='https://iren.gcs-web.com/news-releases/news-release-details/iren-reports-fy26-results';
const pdfUrl='https://iren.gcs-web.com/static-files/1cb9f4da-d4c7-4510-8bda-e475022b59f5';
const cfo='Net cash from (used in) operating activities';
const ppe='Payments for property, plant and equipment net of computer hardware';
const hardware='Payments for computer hardware';
function number(raw:string){
 const negative=raw.startsWith('(')&&raw.endsWith(')');
 const text=negative?raw.slice(1,-1):raw;
 if(!/^(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$/.test(text))throw Error('ערך מקור חסר או לא תקין');
 const value=Number(text.replaceAll(',',''))*(negative?-1:1);
 if(!Number.isFinite(value))throw Error('ערך מקור לא סופי');
 return value;
}
/** A deliberately bounded adapter for the checked FY26 source extract; no inferred PDF columns. */
export function extractIrenFy26(input:unknown){
 const observations:IrenObservation[]=[],issues:{id:IrenMetricId|'source';reason:string}[]=[];
 const x=input as Source;
 if(!x||x.version!==1||x.companyId!=='candidate-iren'||x.title!=='IREN Reports FY26 Results'||x.sourceUrl!==sourceUrl||x.pdfUrl!==pdfUrl||x.reviewStatus!=='pending-analyst-review'||!validDate(x.checkedDate)||x.publishedDate!=='2026-08-27'||!Array.isArray(x.tables))return {observations,issues:[{id:'source' as const,reason:'מקור IREN FY26 חסר או אינו תואם לעותק שנבדק'}]};
 const rules:{id:IrenMetricId;title:string;statement:string;page:number;labels:string[];basis:string;definition:string}[]=[
  {id:'revenue',title:'הכנסות מאוחדות',statement:'Consolidated Statement of Operations',page:12,labels:['Total Revenue'],basis:'consolidated revenue',definition:'הכנסות GAAP מאוחדות של AI וכריית ביטקוין; אינן ARR.'},
  {id:'cashflow',title:'תזרים מפעילות שוטפת',statement:'Consolidated Statement of Cashflows',page:14,labels:[cfo],basis:'reported operating cash flow including customer advances',definition:'תזרים תפעולי מדווח לפי GAAP, כולל השפעת שינוי במקדמות ובהכנסות נדחות; אינו תזרים מנורמל.'},
  {id:'capex',title:'CAPEX לרכוש קבוע וחומרה',statement:'Consolidated Statement of Cashflows',page:14,labels:[ppe,hardware],basis:'cash payments for PPE and computer hardware',definition:'סכום מחושב של שני תשלומי מזומן: רכוש קבוע ללא חומרת מחשוב וחומרת מחשוב. מוצג כהוצאה חיובית; אינו שורת CAPEX כוללת בדוח. אינו כולל נכסים בלתי מוחשיים, מקדמות ופיקדונות, רכישות חברות או השקעות לא במזומן.'},
 ];
 for(const rule of rules)try{
  const tables=x.tables.filter(t=>t.statement===rule.statement);
  if(tables.length!==1)throw Error('טבלת מקור חסרה או כפולה');
  const t=tables[0];
  if(t.unit!=='US$m')throw Error('יחידת המקור אינה מיליוני דולר');
  if(t.periodKind!=='Year ended'||t.periodEnd!=='June 30, 2026'||t.pdfPage!==rule.page)throw Error('תקופת המקור או מיקום העמוד אינם FY26 שנבדק');
  if(!Array.isArray(t.rows))throw Error('שורות מקור חסרות');
  const sourceValues=rule.labels.map(label=>{
   const rows=t.rows.filter(r=>r.label===label);
   if(!rows.length)throw Error('סעיף מקור חסר: '+label);
   if(new Set(rows.map(r=>r.current)).size!==1)throw Error('ערכי מקור סותרים: '+label);
   return {label,raw:rows[0].current,value:number(rows[0].current)};
  });
  if(rule.id==='capex'&&sourceValues.some(v=>v.value>0))throw Error('סימן תשלומי ההשקעה אינו תואם למקור');
  const value=rule.id==='capex'?Math.round(-sourceValues.reduce((s,v)=>s+v.value,0)*10)/10:sourceValues[0].value;
  observations.push({id:rule.id,title:rule.title,point:{value,period:'FY2026',unit:'USD million',basis:rule.basis},periodEnd:'2026-06-30',periodText:'שנה שהסתיימה ב־30.06.2026',definition:rule.definition,sourceValues,sourceUrl:x.sourceUrl,pdfUrl:x.pdfUrl,pdfPage:t.pdfPage,checkedDate:x.checkedDate,publishedDate:x.publishedDate,verification:rule.id==='capex'?'derived-source-checked-pending-review':'source-checked-pending-review'});
 }catch(e){issues.push({id:rule.id,reason:(e as Error).message});}
 return {observations,issues};
}

/** Read the existing base scenario without changing any model inputs or targets. */
export function irenPulseForecasts():Record<IrenMetricId,IrenForecast>{
 const base=model.scenarios.find(s=>s.id==='base')!;
 const forecasts={
  revenue:{point:{value:base.inputs.revenue,period:'2027',unit:'USD million',basis:'consolidated revenue'},description:'הכנסות לשנה הקלנדרית 2027 · תרחיש בסיס',definition:'הכנסות AI וכרייה מוכרות לפי המודל הקיים.'},
  cashflow:{point:{value:base.inputs.operatingCash,period:'2026-07-01/2027-10-19',unit:'USD million',basis:'operating cash flow excluding net customer advances'},description:'יולי 2026 עד 19.10.2027 · תרחיש בסיס',definition:'תזרים במודל המימון לאחר ריבית ומס; השינוי במקדמות לקוחות מחושב בנפרד.'},
  capex:{point:{value:base.inputs.capex,period:'2026-07-01/2027-10-19',unit:'USD million',basis:'model total capex unreconciled'},description:'יולי 2026 עד 19.10.2027 · תרחיש בסיס',definition:'סך CAPEX במודל המימון; טרם הושלם גישור להיקף שני סעיפי המזומן בדוח.'},
 };
 return Object.fromEntries(Object.entries(forecasts).map(([id,forecast])=>[id,{...forecast,asOf:model.analysisDate}])) as Record<IrenMetricId,IrenForecast>;
}
export function compareIrenForecast(observation:IrenObservation,forecast:IrenForecast){
 const reasons:string[]=[];
 const knownDates=validDate(forecast.asOf)&&validDate(observation.publishedDate);
 const precededReport=knownDates&&forecast.asOf<observation.publishedDate;
 if(!precededReport)reasons.push(knownDates?`הדוח פורסם ב־${observation.publishedDate}, לפני או ביום כתיבת המודל (${forecast.asOf}). זהו נתון בסיס, לא הפתעה מול תחזית מוקדמת.`:'לא ניתן לאמת שהתחזית נקבעה לפני פרסום התוצאה.');
 const result=precededReport?metricComparison(observation.point,forecast.point):{status:'timing' as const,label:'נתון בסיס · אין בדיקת הפתעה בדיעבד'};
 if(observation.point.period!==forecast.point.period)reasons.push(`תקופות שונות: ${observation.point.period} בדוח מול ${forecast.description}.`);
 if(observation.point.unit!==forecast.point.unit)reasons.push('יחידות המדידה אינן תואמות.');
 if(observation.point.basis!==forecast.point.basis)reasons.push(`הגדרות שונות: ${observation.definition} מול ${forecast.definition}`);
 return {result,reasons};
}
export const irenFy26=extractIrenFy26(source);
