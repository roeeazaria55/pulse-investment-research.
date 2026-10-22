import source from '../../public/data/dlo-q2-2026-source.json';
import {extractFinancialResults,type FinancialSourceConfig,type FinancialForecast} from './financialResults';
import {thesisMonitorFor} from './thesisMonitoring';

export type DloMetricId='revenue'|'grossProfit'|'profit'|'capex';
const official='https://dlocal.gcs-web.com/news-releases/news-release-details/dlocal-reports-second-quarter-2026-financial-results';
const config:FinancialSourceConfig<DloMetricId>={
 companyId:'us-dlo-nasdaq-a',title:'dLocal Reports Second Quarter 2026 Financial Results',
 sourceUrl:official,documentUrl:official,documentKey:'documentUrl',publishedDate:'2026-08-13',
 period:'2026-Q2',periodStart:'2026-04-01',periodEnd:'2026-06-30',periodText:'01.04.2026–30.06.2026 · רבעון שני',
 sourcePeriodStart:'April 1, 2026',sourcePeriodEnd:'June 30, 2026',sourcePeriodKind:'Three months ended',
 sourceUnit:'USD million',unit:'USD million',multiplier:1,
 rules:[
  {id:'revenue',title:'הכנסות',statement:'Key Performance metrics',labels:['Revenue'],basis:'issuer rounded reported revenue',definition:'הכנסות על פי טבלת ביצועי המנפיק במיליוני דולר, בעיגול לעשירית; סכום החשבונאי המדויק מדווח בנפרד בדוחות IFRS. אינן TPV.'},
  {id:'grossProfit',title:'רווח גולמי',statement:'Key Performance metrics',labels:['Gross Profit'],basis:'issuer rounded gross profit',definition:'רווח גולמי מדווח בעיגול לעשירית מיליון; אינו GP/TPV או מרווח גולמי.'},
  {id:'profit',title:'רווח תפעולי',statement:'Key Performance metrics',labels:['Operating Profit'],basis:'issuer rounded operating profit',definition:'רווח תפעולי בדיווח המנפיק בעיגול לעשירית מיליון, לא Adjusted EBITDA.'},
  {id:'capex',title:'השקעות הוניות מדווחות',statement:'Adjusted Free Cash Flow reconciliation',labels:['Capital expenditures'],basis:'issuer definition acquisitions PPE plus intangible additions',definition:'סעיף Capital expenditures לפי גישור Adjusted FCF, הכולל רכישות רכוש קבוע ותוספות נכסים בלתי מוחשיים; אינו Adjusted Free Cash Flow או תזרים IFRS מפעילות שוטפת.',sourceUnit:'USD thousands',multiplier:0.001,transform:'negative-sum'},
 ]
};
export const extractDloQ22026=(input:unknown)=>extractFinancialResults(input,config);
export const dloQ22026=extractDloQ22026(source);
export function dloPulseForecasts():Partial<Record<DloMetricId,FinancialForecast>>{
 const monitor=thesisMonitorFor(config.companyId);
 if(!monitor)return {};
 return Object.fromEntries(monitor.metrics.filter(m=>m.target).map(m=>[m.id,{companyId:config.companyId,point:m.target!,description:m.expectation,definition:m.target!.basis,asOf:monitor.asOf}]));
}
