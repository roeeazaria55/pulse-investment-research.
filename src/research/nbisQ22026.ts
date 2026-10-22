import source from '../../public/data/nbis-q2-2026-source.json';
import {extractFinancialResults,type FinancialSourceConfig,type FinancialForecast} from './financialResults';
import {thesisMonitorFor} from './thesisMonitoring';

export type NbisMetricId='revenue'|'profit'|'cashflow'|'capex';
const config:FinancialSourceConfig<NbisMetricId>={
 companyId:'candidate-nebius',title:'Nebius Group N.V. Q2 2026 Financial Results, SEC Exhibit 99.1',
 sourceUrl:'https://nebius.com/newsroom/nebius-reports-second-quarter-2026-financial-results',
 documentUrl:'https://www.sec.gov/Archives/edgar/data/1513845/000110465926094568/tm2622968d1_ex99-1.htm',
 documentKey:'documentUrl',publishedDate:'2026-08-12',
 resultsPublishedDate:'2026-08-12',resultsSourceUrl:'https://nebius.com/newsroom/nebius-reports-second-quarter-2026-financial-results',
 period:'2026-Q2',periodStart:'2026-04-01',periodEnd:'2026-06-30',periodText:'01.04.2026–30.06.2026 · רבעון שני',
 sourcePeriodStart:'April 1, 2026',sourcePeriodEnd:'June 30, 2026',sourcePeriodKind:'Three months ended',
 sourceUnit:'USD million',unit:'USD million',multiplier:1,
 rules:[
  {id:'revenue',title:'הכנסות מאוחדות',statement:'Unaudited Condensed Consolidated Statements of Operations',page:7,labels:['Revenues'],basis:'consolidated revenue',definition:'הכנסות מאוחדות מדווחות של קבוצת Nebius, כולל עסקים נוספים מעבר ל־AI Cloud; אינן ARR או צבר הזמנות.'},
  {id:'profit',title:'הפסד תפעולי',statement:'Unaudited Condensed Consolidated Statements of Operations',page:7,labels:['Loss from operations'],basis:'GAAP operating income (loss)',definition:'הפסד תפעולי מאוחד חשבונאי בסימן שלילי. אינו Adjusted EBITDA או EBITDA של חטיבת AI Cloud.'},
  {id:'cashflow',title:'תזרים מפעילות שוטפת',statement:'Unaudited Condensed Consolidated Statements of Cash Flows',page:8,labels:['Net cash provided by / (used in) operating activities'],basis:'reported operating cash flow',definition:'תזרים תפעולי מדווח לרבעון, הכולל השפעת מקדמות לקוחות ושינוי בהכנסות נדחות; אינו תזרים מנורמל.'},
  {id:'capex',title:'תשלומי רכוש קבוע ונכסים בלתי מוחשיים',statement:'Unaudited Condensed Consolidated Statements of Cash Flows',page:8,labels:['Purchases of property and equipment and intangible assets'],basis:'cash purchases PPE and intangible assets',definition:'תשלומי מזומן לרכוש קבוע ולנכסים בלתי מוחשיים בלבד; מוצגים כהוצאה חיובית. אינם סך התחייבויות CAPEX, השקעות לא במזומן או עלות קיבולת עתידית.',transform:'negative-sum'},
 ]
};
export const extractNbisQ22026=(input:unknown)=>extractFinancialResults(input,config);
export const nbisQ22026=extractNbisQ22026(source);
export function nbisPulseForecasts():Partial<Record<NbisMetricId,FinancialForecast>>{
 const monitor=thesisMonitorFor(config.companyId);
 if(!monitor)return {};
 return Object.fromEntries(monitor.metrics.filter(m=>m.target).map(m=>[m.id,{companyId:config.companyId,point:m.target!,description:m.expectation,definition:m.target!.basis,asOf:monitor.asOf}]));
}
