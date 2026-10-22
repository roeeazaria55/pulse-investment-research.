import {metricComparison,type MetricPoint} from './thesisMonitoring';
import {validDate} from './exchange';

export interface FinancialObservation<Id extends string=string> {
 id:Id;companyId:string;title:string;point:MetricPoint;periodStart:string;periodEnd:string;periodText:string;
 definition:string;sourceValues:{label:string;raw:string;value:number}[];sourceUnit:string;
 sourceUrl:string;documentUrl:string;locationUrl:string;locationLabel:string;
 checkedDate:string;publishedDate:string;resultsPublishedDate:string;
 verification:'source-checked-pending-review'|'derived-source-checked-pending-review';
}
export interface FinancialForecast {companyId:string;point:MetricPoint;description:string;definition:string;asOf:string}
export interface FinancialResult<Id extends string=string> {observations:FinancialObservation<Id>[];issues:{id:Id|'source';reason:string}[]}
export interface FinancialRule<Id extends string=string> {
 id:Id;title:string;statement:string;page?:number;labels:string[];basis:string;definition:string;
 transform?:'negative-sum';sourceUnit?:string;multiplier?:number;
}
export interface FinancialSourceConfig<Id extends string=string> {
 companyId:string;title:string;sourceUrl:string;documentUrl:string;documentKey:'pdfUrl'|'documentUrl';publishedDate:string;resultsPublishedDate?:string;resultsSourceUrl?:string;
 period:string;periodStart:string;periodEnd:string;periodText:string;sourcePeriodEnd:string;sourcePeriodStart?:string;
 sourcePeriodKind:string;sourceUnit:string;unit:string;multiplier:number;rules:FinancialRule<Id>[];
}
type Table={statement:string;unit:string;periodKind:string;periodStart?:string;periodEnd:string;pdfPage?:number;page?:number;rows:{label:string;current:string}[]};
type Source={version:number;companyId:string;title:string;sourceUrl:string;pdfUrl?:string;documentUrl?:string;checkedDate:string;publishedDate:string;resultsPublishedDate?:string;resultsSourceUrl?:string;reviewStatus:string;revised?:boolean;tables:Table[]};

/** Strict source-cell parsing; unsupported formats must be reviewed rather than coerced. */
export function parseSourceNumber(raw:string){
 if(typeof raw!=='string')throw Error('ערך מקור חסר או לא תקין');
 const negative=raw.startsWith('(')&&raw.endsWith(')');
 const text=negative?raw.slice(1,-1):raw;
 if(!/^(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$/.test(text))throw Error('ערך מקור חסר או לא תקין');
 const value=Number(text.replaceAll(',',''))*(negative?-1:1);
 if(!Number.isFinite(value))throw Error('ערך מקור לא סופי');
 return value;
}

/** One bounded table adapter, with issuer-specific identities/headers/definitions supplied as rules.
 * A saved extract is evidence of a checked read, not a full archive or a live refresh.
 */
export function extractFinancialResults<Id extends string>(input:unknown,config:FinancialSourceConfig<Id>):FinancialResult<Id>{
 const observations:FinancialObservation<Id>[]=[],issues:FinancialResult<Id>['issues']=[];
 const x=input as Source;
 if(!x||x.version!==1||x.companyId!==config.companyId||x.title!==config.title||x.sourceUrl!==config.sourceUrl||x[config.documentKey]!==config.documentUrl||x.reviewStatus!=='pending-analyst-review'||x.revised===true||!validDate(x.checkedDate)||x.publishedDate!==config.publishedDate||x.checkedDate<x.publishedDate||!Array.isArray(x.tables))return {observations,issues:[{id:'source',reason:'מקור חסר או אינו תואם לעותק שנבדק; נדרשת בדיקת מקור'}]};
 if(config.resultsPublishedDate&&(x.resultsPublishedDate!==config.resultsPublishedDate||x.resultsSourceUrl!==config.resultsSourceUrl))return {observations,issues:[{id:'source',reason:'מועד פרסום התוצאות או מקורו אינם תואמים לתיעוד שנבדק'}]};
 for(const rule of config.rules)try{
  const tables=x.tables.filter(t=>t?.statement===rule.statement);
  if(tables.length!==1)throw Error('טבלת מקור חסרה או כפולה');
  const t=tables[0];
  if(t.unit!==(rule.sourceUnit??config.sourceUnit))throw Error('יחידת המקור אינה תואמת ליחידה שנבדקה: '+(rule.sourceUnit??config.sourceUnit));
  if(t.periodKind!==config.sourcePeriodKind||t.periodEnd!==config.sourcePeriodEnd||(config.sourcePeriodStart!==undefined&&t.periodStart!==config.sourcePeriodStart)||(rule.page!==undefined&&(t.pdfPage??t.page)!==rule.page))throw Error('תקופת המקור או מיקום העמוד אינם תואמים לדוח שנבדק');
  if(!Array.isArray(t.rows))throw Error('שורות מקור חסרות');
  const sourceValues=rule.labels.map(label=>{
   const rows=t.rows.filter(r=>r?.label===label);
   if(!rows.length)throw Error('סעיף מקור חסר: '+label);
   if(new Set(rows.map(r=>r.current)).size!==1)throw Error('ערכי מקור סותרים: '+label);
   return {label,raw:rows[0].current,value:parseSourceNumber(rows[0].current)};
  });
  const derived=rule.transform==='negative-sum';
  if(derived&&sourceValues.some(v=>v.value>0))throw Error('סימן תשלומי ההשקעה אינו תואם למקור');
  const rawValue=derived?-sourceValues.reduce((s,v)=>s+v.value,0):sourceValues[0].value;
  const value=Math.round(rawValue*(rule.multiplier??config.multiplier)*1e6)/1e6;
  if(!Number.isFinite(value))throw Error('ערך מקור לא סופי');
  const pdf=config.documentKey==='pdfUrl';
  observations.push({id:rule.id,companyId:x.companyId,title:rule.title,point:{value,period:config.period,unit:config.unit,basis:rule.basis},periodStart:config.periodStart,periodEnd:config.periodEnd,periodText:config.periodText,definition:rule.definition,sourceValues,sourceUnit:t.unit,sourceUrl:x.sourceUrl,documentUrl:config.documentUrl,locationUrl:pdf&&rule.page!==undefined?`${config.documentUrl}#page=${rule.page}`:`${config.documentUrl}#:~:text=${encodeURIComponent(rule.statement)}`,locationLabel:pdf&&rule.page!==undefined?`PDF עמוד ${rule.page}`:rule.page!==undefined?`דוח רשמי עמוד ${rule.page} · ${rule.statement}`:`דוח רשמי · ${rule.statement}`,checkedDate:x.checkedDate,publishedDate:x.publishedDate,resultsPublishedDate:config.resultsPublishedDate??x.publishedDate,verification:derived?'derived-source-checked-pending-review':'source-checked-pending-review'});
 }catch(e){issues.push({id:rule.id,reason:(e as Error).message});}
 return {observations,issues};
}

/** Same-day forecasts are blocked: a date alone cannot establish intraday ordering. */
export function compareDatedMetric(observed:MetricPoint|null,target:MetricPoint|null,asOf:string,publishedDate:string|null){
 if(!observed||!target)return metricComparison(observed,target);
 if(!validDate(asOf)||!validDate(publishedDate)||asOf>=publishedDate!)return {status:'timing' as const,label:'נתון בסיס · אין בדיקת הפתעה בדיעבד'};
 return metricComparison(observed,target);
}
export function compareFinancialForecast(observation:FinancialObservation,forecast:FinancialForecast|undefined){
 const reasons:string[]=[];
 if(!forecast)return {result:metricComparison(observation.point,null),reasons:['לא הוגדרה במחקר תחזית מספרית למדד זה בתקופה ובהגדרה המתאימות.']};
 if(forecast.companyId!==observation.companyId)return {result:{status:'company' as const,label:'חברות שונות'},reasons:['התחזית והנתון המדווח אינם שייכים לאותה חברה.']};
 const result=compareDatedMetric(observation.point,forecast.point,forecast.asOf,observation.resultsPublishedDate);
 if(result.status==='timing'){
  const knownDates=validDate(forecast.asOf)&&validDate(observation.resultsPublishedDate);
  reasons.push(knownDates?`התוצאה פורסמה ב־${observation.resultsPublishedDate}, לפני או ביום כתיבת המודל (${forecast.asOf}). זהו נתון בסיס, לא הפתעה מול תחזית מוקדמת.`:'לא ניתן לאמת שהתחזית נקבעה לפני פרסום התוצאה.');
 }
 if(observation.point.period!==forecast.point.period)reasons.push(`תקופות שונות: ${observation.point.period} בדוח מול ${forecast.description}.`);
 if(observation.point.unit!==forecast.point.unit)reasons.push('יחידות המדידה אינן תואמות.');
 if(observation.point.basis!==forecast.point.basis)reasons.push(`הגדרות שונות: ${observation.definition} מול ${forecast.definition}`);
 return {result,reasons};
}
