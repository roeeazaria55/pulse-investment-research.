import type {IntakeDocument} from '../data/reportIntake';
export interface ReviewBaseline {companyId:string;ticker:string;asOf:string;sourceUrls:readonly string[];horizon?:string}
export interface ModelReviewSignal {id:string;companyId:string;ticker:string;reason:string;sourceUrl?:string;date:string}
const day=(s:string)=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const date=new Date(s+'T00:00:00Z');return Number.isFinite(date.getTime())&&date.toISOString().slice(0,10)===s;};
/** A reason to inspect assumptions, never an automatic valuation conclusion. */
export function modelReviewSignals(baselines:readonly ReviewBaseline[],documents:readonly IntakeDocument[],today=new Date().toISOString().slice(0,10)):ModelReviewSignal[]{
 const result:ModelReviewSignal[]=[];
 for(const b of baselines){
  if(!day(b.asOf))continue;
  const docs=documents.filter(d=>d.companyId===b.companyId&&d.status==='extracted'&&d.publishedDate&&day(d.publishedDate)&&d.publishedDate>b.asOf&&d.publishedDate<=today&&!b.sourceUrls.includes(d.url));
  docs.sort((a,b)=>b.publishedDate!.localeCompare(a.publishedDate!));
  const revised=documents.find(d=>d.companyId===b.companyId&&d.status==='extracted'&&d.revised&&b.sourceUrls.includes(d.url)&&d.revisions.some(r=>r.lastSuccessfulAt.slice(0,10)>b.asOf&&r.lastSuccessfulAt<d.lastSuccessfulAt));
  const latest=docs[0];
  if(latest)result.push({id:`report:${b.companyId}:${b.asOf}:${latest.sha256}`,companyId:b.companyId,ticker:b.ticker,reason:'נקלט דוח שפורסם אחרי המחקר — יש לבדוק את ההנחות מולו.',sourceUrl:latest.url,date:latest.publishedDate!});
  else if(revised)result.push({id:`revision:${b.companyId}:${b.asOf}:${revised.sha256}`,companyId:b.companyId,ticker:b.ticker,reason:'גרסת מקור ששימשה במחקר השתנתה מאז — יש לבדוק אם השינוי מהותי למודל.',sourceUrl:revised.url,date:revised.lastSuccessfulAt.slice(0,10)});
  else if(b.horizon&&day(b.horizon)&&b.horizon<today)result.push({id:`horizon:${b.companyId}:${b.horizon}`,companyId:b.companyId,ticker:b.ticker,reason:'אופק השווי השמור הסתיים — יש לבדוק תקופה והנחות מחדש.',date:b.horizon});
 }
 return result.sort((a,b)=>b.date.localeCompare(a.date));
}
