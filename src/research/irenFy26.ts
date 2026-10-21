import source from '../../public/data/iren-fy26-source.json';
import model from '../data/models/iren.json';
import {extractFinancialResults,compareFinancialForecast,type FinancialObservation,type FinancialForecast,type FinancialSourceConfig} from './financialResults';

export type IrenMetricId='revenue'|'cashflow'|'capex';
export type IrenObservation=FinancialObservation<IrenMetricId>;
export type IrenForecast=FinancialForecast;
const config:FinancialSourceConfig<IrenMetricId>={
 companyId:'candidate-iren',title:'IREN Reports FY26 Results',
 sourceUrl:'https://iren.gcs-web.com/news-releases/news-release-details/iren-reports-fy26-results',
 documentUrl:'https://iren.gcs-web.com/static-files/1cb9f4da-d4c7-4510-8bda-e475022b59f5',documentKey:'pdfUrl',publishedDate:'2026-08-27',
 period:'FY2026',periodStart:'2025-07-01',periodEnd:'2026-06-30',periodText:'שנה שהסתיימה ב־30.06.2026',
 sourcePeriodEnd:'June 30, 2026',sourcePeriodKind:'Year ended',sourceUnit:'US$m',unit:'USD million',multiplier:1,
 rules:[
  {id:'revenue',title:'הכנסות מאוחדות',statement:'Consolidated Statement of Operations',page:12,labels:['Total Revenue'],basis:'consolidated revenue',definition:'הכנסות GAAP מאוחדות של AI וכריית ביטקוין; אינן ARR.'},
  {id:'cashflow',title:'תזרים מפעילות שוטפת',statement:'Consolidated Statement of Cashflows',page:14,labels:['Net cash from (used in) operating activities'],basis:'reported operating cash flow including customer advances',definition:'תזרים תפעולי מדווח לפי GAAP, כולל השפעת שינוי במקדמות ובהכנסות נדחות; אינו תזרים מנורמל.'},
  {id:'capex',title:'CAPEX לרכוש קבוע וחומרה',statement:'Consolidated Statement of Cashflows',page:14,labels:['Payments for property, plant and equipment net of computer hardware','Payments for computer hardware'],basis:'cash payments for PPE and computer hardware',transform:'negative-sum',definition:'סכום מחושב של שני תשלומי מזומן: רכוש קבוע ללא חומרת מחשוב וחומרת מחשוב. מוצג כהוצאה חיובית; אינו שורת CAPEX כוללת בדוח. אינו כולל נכסים בלתי מוחשיים, מקדמות ופיקדונות, רכישות חברות או השקעות לא במזומן.'},
 ],
};
export const extractIrenFy26=(input:unknown)=>extractFinancialResults(input,config);
export const compareIrenForecast=compareFinancialForecast;

/** Read the existing base scenario without changing any model inputs or targets. */
export function irenPulseForecasts():Record<IrenMetricId,IrenForecast>{
 const base=model.scenarios.find(s=>s.id==='base')!;
 const forecasts={
  revenue:{point:{value:base.inputs.revenue,period:'2027',unit:'USD million',basis:'consolidated revenue'},description:'הכנסות לשנה הקלנדרית 2027 · תרחיש בסיס',definition:'הכנסות AI וכרייה מוכרות לפי המודל הקיים.'},
  cashflow:{point:{value:base.inputs.operatingCash,period:'2026-07-01/2027-10-19',unit:'USD million',basis:'operating cash flow excluding net customer advances'},description:'יולי 2026 עד 19.10.2027 · תרחיש בסיס',definition:'תזרים במודל המימון לאחר ריבית ומס; השינוי במקדמות לקוחות מחושב בנפרד.'},
  capex:{point:{value:base.inputs.capex,period:'2026-07-01/2027-10-19',unit:'USD million',basis:'model total capex unreconciled'},description:'יולי 2026 עד 19.10.2027 · תרחיש בסיס',definition:'סך CAPEX במודל המימון; טרם הושלם גישור להיקף שני סעיפי המזומן בדוח.'},
 };
 return Object.fromEntries(Object.entries(forecasts).map(([id,forecast])=>[id,{...forecast,companyId:config.companyId,asOf:model.analysisDate}])) as Record<IrenMetricId,IrenForecast>;
}
export const irenFy26=extractIrenFy26(source);
