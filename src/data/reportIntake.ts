import {officialRegistry} from './official';
import {validDate,safeSource} from '../research/exchange';
export interface IntakeFact {concept:string;value:number;unit:string;start:string|null;end:string;context:string;status:'structured-source';definition:string}
export interface IntakeTable {rows:string[][];spans:boolean;scope:string;page:number|null}
export interface IntakeDocument {id:string;companyId:string;ticker:string;title:string;url:string;finalUrl:string;publishedDate:string|null;documentPeriod:string|null;periodBasis:string;sha256:string;bytes:number;format:'html'|'pdf';pages:number|null;readScope:'full-body'|'partial-pages';charactersRead:number;status:'extracted'|'read-no-supported-data';tables:IntakeTable[];tableCount:number;tablesTruncated:boolean;facts:IntakeFact[];reviewStatus:'pending-review';firstDetectedAt:string;lastSuccessfulAt:string;lastAttemptAt:string;revised:boolean;revisions:{sha256:string;firstDetectedAt:string;lastSuccessfulAt:string}[];parserVersion:string;error:string|null;notice:string}
export interface IntakeSource {companyId:string;lastAttemptAt:string;status:'ok'|'partial'|'failed'|'deferred'|'no-candidates';error:string|null}
export interface ReportIntakeSnapshot {version:1;generatedAt:string;parserVersion:string;documents:IntakeDocument[];sources:IntakeSource[];notice:string}
const stamp=(x:unknown):x is string=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T/.test(x)&&Number.isFinite(Date.parse(x));
const text=(x:unknown,max=600):x is string=>typeof x==='string'&&x.length>0&&x.length<=max;
const optionalText=(x:unknown,max=600)=>x===null||text(x,max);
const hash=(x:unknown)=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
function approved(url:string,id:string){
 const c=officialRegistry.companies.find(c=>c.id===id);if(!c||!safeSource(url))return false;
 const u=new URL(url);let path:string;try{path=decodeURIComponent(u.pathname);}catch{return false;}
 return !u.hash&&!path.split('/').some(p=>p==='.'||p==='..')&&c.allowedHosts.includes(u.hostname)&&c.documentPaths.some(p=>u.pathname.startsWith(p));
}
export function parseReportIntake(value:unknown):ReportIntakeSnapshot{
 const x=value as ReportIntakeSnapshot;
 if(!x||x.version!==1||!stamp(x.generatedAt)||!text(x.parserVersion)||!text(x.notice,1000)||!Array.isArray(x.documents)||x.documents.length>officialRegistry.companies.length*6||!Array.isArray(x.sources))throw Error('Invalid report intake');
 const known=new Set(officialRegistry.companies.map(c=>c.id));const sourceIds=new Set<string>();
 for(const s of x.sources){if(!known.has(s.companyId)||sourceIds.has(s.companyId)||!stamp(s.lastAttemptAt)||!['ok','partial','failed','deferred','no-candidates'].includes(s.status)||!optionalText(s.error,180))throw Error('Invalid intake status');sourceIds.add(s.companyId);}
 const ids=new Set<string>();
 for(const d of x.documents){
  if(!known.has(d.companyId)||ids.has(d.id)||!/^report:[a-f0-9]{32}$/.test(d.id)||!text(d.title)||!approved(d.url,d.companyId)||!approved(d.finalUrl,d.companyId)||!hash(d.sha256)||!['html','pdf'].includes(d.format)||!['full-body','partial-pages'].includes(d.readScope)||!['extracted','read-no-supported-data'].includes(d.status)||d.reviewStatus!=='pending-review'||!Number.isInteger(d.bytes)||d.bytes<1||d.bytes>8*1024*1024||!Number.isInteger(d.charactersRead)||d.charactersRead<100||!stamp(d.firstDetectedAt)||!stamp(d.lastSuccessfulAt)||!stamp(d.lastAttemptAt)||!optionalText(d.error,180)||d.publishedDate!==null&&!validDate(d.publishedDate)||!Array.isArray(d.tables)||d.tables.length>12||!Array.isArray(d.facts)||d.facts.length>150||!Array.isArray(d.revisions)||d.revisions.length>3||typeof d.revised!=='boolean'||!Number.isInteger(d.tableCount)||d.tableCount<d.tables.length||typeof d.tablesTruncated!=='boolean'||!text(d.notice,1000)||!text(d.parserVersion)||!optionalText(d.documentPeriod,160))throw Error('Invalid report document');
  for(const t of d.tables)if(!Array.isArray(t.rows)||t.rows.length>35||!t.rows.every(row=>Array.isArray(row)&&row.length<=16&&row.every(cell=>typeof cell==='string'&&cell.length<=250))||typeof t.spans!=='boolean'||!text(t.scope)||!(t.page===null||Number.isInteger(t.page)&&t.page>0))throw Error('Invalid report table');
  for(const f of d.facts)if(!text(f.concept)||!Number.isFinite(f.value)||!text(f.unit,160)||!(f.start===null||validDate(f.start))||!validDate(f.end)||f.start!==null&&f.start>f.end||!text(f.context)||f.status!=='structured-source'||!text(f.definition))throw Error('Invalid structured fact');
  for(const r of d.revisions)if(!hash(r.sha256)||!stamp(r.firstDetectedAt)||!stamp(r.lastSuccessfulAt))throw Error('Invalid report revision');
  ids.add(d.id);
 }
 return x;
}
