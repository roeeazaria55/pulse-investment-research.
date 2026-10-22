import source from '../../public/data/smci-fy26-source.json';
import {extractFinancialResults,type FinancialSourceConfig,type FinancialForecast} from './financialResults';
import {thesisMonitorFor} from './thesisMonitoring';

export type SmciMetricId='revenue'|'profit'|'cashflow';
const config:FinancialSourceConfig<SmciMetricId>={
 companyId:'us-smci-nasdaq-common',title:'Super Micro Computer, Inc. FY2026 Form 10-K',
 sourceUrl:'https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/0001375365-26-000022-index.html',
 documentUrl:'https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm',documentKey:'documentUrl',publishedDate:'2026-08-31',
 resultsPublishedDate:'2026-08-11',resultsSourceUrl:'https://ir.supermicro.com/news/news-details/2026/Supermicro-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Financial-Results/default.aspx',
 period:'FY2026',periodStart:'2025-07-01',periodEnd:'2026-06-30',periodText:'01.07.2025–30.06.2026 · שנה פיסקלית מלאה',
 sourcePeriodStart:'July 1, 2025',sourcePeriodEnd:'June 30, 2026',sourcePeriodKind:'Years ended',sourceUnit:'USD thousands',unit:'USD million',multiplier:0.001,
 rules:[
  {id:'revenue',title:'הכנסות מאוחדות',statement:'CONSOLIDATED STATEMENTS OF OPERATIONS',page:59,labels:['Net sales (including related party sales of $29,781, $42,259, and $69,791 in fiscal years 2026, 2025, and 2024, respectively)'],basis:'revenue',definition:'Net sales מאוחדות לפי US GAAP, כולל מכירות לצדדים קשורים. אינן הזמנות, Backlog או תחזית הנהלה.'},
  {id:'profit',title:'רווח תפעולי',statement:'CONSOLIDATED STATEMENTS OF OPERATIONS',page:59,labels:['Income from operations'],basis:'operating income',definition:'רווח תפעולי מאוחד מדווח לפי US GAAP; אינו EBITDA או רווח מתואם.'},
  {id:'cashflow',title:'תזרים מפעילות שוטפת',statement:'CONSOLIDATED STATEMENTS OF CASH FLOWS',page:63,labels:['Net cash (used in) provided by operating activities'],basis:'operating cash flow',definition:'תזרים מזומנים מאוחד ששימש לפעילות שוטפת לפי US GAAP, כולל שינויים בהון חוזר ובהכנסות נדחות. ערך שלילי הוא שימוש במזומן; אינו FCF או תזרים מנורמל.'},
 ],
};
export const extractSmciFy26=(input:unknown)=>extractFinancialResults(input,config);
export const smciFy26=extractSmciFy26(source);
/** Existing research targets retain their original units and definitions. No implicit bridging. */
export function smciPulseForecasts():Partial<Record<SmciMetricId,FinancialForecast>>{
 const monitor=thesisMonitorFor(config.companyId)!;
 return Object.fromEntries(monitor.metrics.filter(m=>m.target).map(m=>[m.id,{companyId:config.companyId,point:m.target!,description:m.expectation,definition:m.target!.basis,asOf:monitor.asOf}]));
}
