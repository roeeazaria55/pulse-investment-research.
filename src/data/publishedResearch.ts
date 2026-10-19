import nbis from './nbis-research.json';
import {parseAnalysis,type AnalysisImport} from '../research/exchange';
import {officialRegistry,type OfficialItem} from './official';
export interface PublishedResearch {period:string;scope:string;analysis:AnalysisImport;}
const datasets=import.meta.glob('./research/*.json',{eager:true,import:'default'}) as Record<string,PublishedResearch>;
const rows=[{period:'Q2 2026 + selected updates through 01.10',scope:'דוחות ועדכוני חברה נבחרים',analysis:nbis},...Object.values(datasets)];
export const publishedResearch:PublishedResearch[]=rows.map(row=>{
 if(!officialRegistry.companies.some(c=>c.id===row.analysis.companyId))throw Error('Unknown published research identity');
 return {...row,analysis:parseAnalysis(JSON.stringify(row.analysis),row.analysis.companyId)};
});
if(new Set(publishedResearch.map(x=>x.analysis.companyId)).size!==publishedResearch.length)throw Error('Duplicate published research');
export function publishedFor(companyId:string){return publishedResearch.find(x=>x.analysis.companyId===companyId);}
export function researchAge(asOf:string,now=new Date()):number|null{
 const time=Date.parse(asOf+'T00:00:00Z');
 return Number.isFinite(time)&&Number.isFinite(now.getTime())?Math.max(0,Math.floor((now.getTime()-time)/86400000)):null;
}
function sourceKey(raw:string){const u=new URL(raw);let path=u.pathname;try{path=decodeURI(path);}catch{/* Keep malformed escapes literal. */}return u.origin+path.replace(/\/$/,'');}
export function pendingResearchSources(pack:AnalysisImport,items:OfficialItem[]){
 const read=new Set(pack.sourceUrls.map(sourceKey));
 const seen=new Set<string>();
 return items.filter(item=>{
  if(item.companyId!==pack.companyId)return false;
  const key=sourceKey(item.url);
  if(read.has(key)||seen.has(key))return false;
  // Not cited does not mean new: keep prior/unknown-date publications visible
  // for review without inferring publication from collection or last-seen time.
  seen.add(key);return true;
 });
}
