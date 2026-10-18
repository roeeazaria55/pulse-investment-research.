import registry from '../../public/data/official-registry.json';
export { registry as officialRegistry };
export interface OfficialItem {
  id: string; companyId: string; ticker: string; title: string; url: string;
  sourceId: string; kind: 'document'|'schedule'|'results'|'release';
  publishedDate: string|null; collectedAt: string; lastSeenAt: string;
  metadataStatus: 'index-link'|'page-metadata'; metadataCheckedAt: string|null;
  metadataError: string|null; contentScope: 'metadata-only';
  sourceKind?:'company-ir'|'issuer-distributed';issuerEvidenceUrl?:string|null;
  titleBasis?:'page-heading'|'link-label'|'index-context'|'filename'; sourceLabel?:string;
  language?:'he'|'en'|null; documentPeriod?:string|null;
  periodBasis?:'index-heading'|'title'|'filename-hint'|'unknown';
  publishedDateBasis?:'page-published-metadata'|'index-time'|'legacy-metadata'|'unknown';dateEvidenceUrl?:string|null;
}
export interface OfficialSource {
  id: string; companyId: string; status: 'ok'|'failed'|'not-checked';
  lastAttemptAt: string|null; lastSuccessfulAt: string|null; count: number; error: string|null;
}
export interface OfficialSnapshot { version: 1; generatedAt: string|null; items: OfficialItem[]; sources: OfficialSource[]; }
const stamp=(x:unknown): x is string => typeof x==='string' && /^\d{4}-\d{2}-\d{2}T/.test(x) && Number.isFinite(Date.parse(x));
const nullableStamp=(x:unknown)=>x===null||stamp(x);
const text=(x:unknown,max=600):x is string=>typeof x==='string'&&x.length>0&&x.length<=max;
export function parseOfficialSnapshot(value: unknown): OfficialSnapshot {
  const f=value as OfficialSnapshot;
  if(!f||f.version!==1||!nullableStamp(f.generatedAt)||!Array.isArray(f.items)||f.items.length>264||!Array.isArray(f.sources))throw Error('Invalid official snapshot');
  const sourceMap=new Map(registry.companies.flatMap(c=>c.sources.map(s=>[s.id,{...s,company:c}])));
  const keys=new Set<string>();
  for(const s of f.sources){
    const known=sourceMap.get(s.id);
    if(!known||known.company.id!==s.companyId||keys.has(s.id)||!['ok','failed','not-checked'].includes(s.status)||!nullableStamp(s.lastAttemptAt)||!nullableStamp(s.lastSuccessfulAt)||!Number.isInteger(s.count)||s.count<0||s.count>8||!(s.error===null||text(s.error,180))||s.status==='ok'&&(!s.count||!stamp(s.lastAttemptAt)||s.lastSuccessfulAt!==s.lastAttemptAt)||s.status==='not-checked'&&(s.lastAttemptAt!==null||s.lastSuccessfulAt!==null||s.count!==0))throw Error('Invalid official source status');
    keys.add(s.id);
  }
  if(keys.size!==sourceMap.size)throw Error('Missing official source statuses');
  const ids=new Set<string>();
  for(const n of f.items){
    const source=sourceMap.get(n.sourceId),company=source?.company;
    const u=new URL(n.url);
    if(!company||n.companyId!==company.id||n.ticker!==company.ticker||!/^official:[a-f0-9]{32}$/.test(n.id)||ids.has(n.id)||!text(n.title)||u.protocol!=='https:'||u.username||u.password||u.port||u.hash||!company.allowedHosts.includes(u.hostname)||!company.documentPaths.some(p=>u.pathname.startsWith(p))||!['document','schedule','results','release'].includes(n.kind)||n.contentScope!=='metadata-only'||!['index-link','page-metadata'].includes(n.metadataStatus)||!stamp(n.collectedAt)||!stamp(n.lastSeenAt)||!nullableStamp(n.metadataCheckedAt)||!(n.metadataError===null||text(n.metadataError,180))||n.publishedDate!==null&&(!/^\d{4}-\d{2}-\d{2}$/.test(n.publishedDate)||!Number.isFinite(Date.parse(n.publishedDate))||new Date(n.publishedDate).toISOString().slice(0,10)!==n.publishedDate))throw Error('Invalid official item attribution');
    if(n.metadataStatus==='page-metadata'&&!stamp(n.metadataCheckedAt))throw Error('Missing page metadata check');
    if(n.sourceKind==='issuer-distributed'&&(!source||!('kind' in source)||source.kind!=='issuer-distributed'||n.issuerEvidenceUrl!==source.url))throw Error('Wrong issuer-distribution proof');
    if(n.sourceKind!==undefined&&!['company-ir','issuer-distributed'].includes(n.sourceKind))throw Error('Invalid source kind');
    if(n.titleBasis!==undefined&&!['page-heading','link-label','index-context','filename'].includes(n.titleBasis)||n.language!==undefined&&n.language!==null&&!['he','en'].includes(n.language)||n.documentPeriod!==undefined&&n.documentPeriod!==null&&!text(n.documentPeriod,160)||n.periodBasis!==undefined&&!['index-heading','title','filename-hint','unknown'].includes(n.periodBasis)||n.sourceLabel!==undefined&&typeof n.sourceLabel!=='string')throw Error('Invalid document description');
    if(n.publishedDateBasis!==undefined){
      if(!['page-published-metadata','index-time','legacy-metadata','unknown'].includes(n.publishedDateBasis))throw Error('Invalid publication evidence');
      if(n.publishedDate!==null){
        if(n.publishedDateBasis==='unknown'||!n.dateEvidenceUrl)throw Error('Missing publication evidence');
        const evidence=new URL(n.dateEvidenceUrl);
        if(evidence.protocol!=='https:'||evidence.username||evidence.password||evidence.port||!company.allowedHosts.includes(evidence.hostname))throw Error('Wrong publication source');
      }else if(n.publishedDateBasis!=='unknown'||n.dateEvidenceUrl)throw Error('Publication claim without date');
    }
    ids.add(n.id);
  }
  return f;
}

export function officialCompany(ticker?:string,name?:string){
 const norm=(s:string)=>s.trim().toLocaleLowerCase();
 if(ticker){const found=registry.companies.find(c=>c.ticker&&norm(c.ticker)===norm(ticker));if(found)return found;}
 if(name)return registry.companies.find(c=>[c.name,c.label,...c.aliases].some(a=>norm(a)===norm(name)));
 return undefined;
}

export function officialTitle(item:OfficialItem){
 const title=item.title.replace(/\s+/g,' ').trim().replace(/[›»↗]+$/,'').trim();
 if(title && !/^(?:(?:ENG|HEB|EN|HE|PDF|View File|Download|Read More|להורדה|עברית|אנגלית)|\W)+$/i.test(title))return title;
 const company=registry.companies.find(c=>c.id===item.companyId);
 let filename='מסמך רשמי';try{filename=decodeURIComponent(new URL(item.url).pathname.split('/').pop()||filename).replace(/[_-]+/g,' ');}catch{/* retain safe fallback */}
 return `${company?.label||company?.name||'חברה'} — ${filename}`;
}
