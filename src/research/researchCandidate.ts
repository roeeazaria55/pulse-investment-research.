import {safeSource,validDate} from './exchange';

/** Candidate-only source pack: no portfolio data, no automatic publication. */
export interface ResearchCandidate {
 version:1;
 companyId:string;
 source:{filename:string;sha256:string;asOf:string;verification:'unverified'|'primary-verified';sourceUrls:string[]};
 valuation:{
  currency:'USD'|'ILS'|'ILA';
  shareUnit:'share'|'ADS';
  reference:{value:number;asOf:string}|null;
  horizon:{date:string;earningsPeriod:string;note:string};
  declaredWeighted:number|null;
  scenarios:{id:'bear'|'base'|'bull';probability:number;statedPrice:number;rationale:string}[];
 };
}
export type CandidateDiff={path:string;before:unknown;after:unknown};
const record=(x:unknown):x is Record<string,unknown>=>!!x&&typeof x==='object'&&!Array.isArray(x);
const finite=(x:unknown)=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
export function validateResearchCandidate(raw:unknown,companyId:string):ResearchCandidate {
 if(!record(raw)||raw.version!==1||raw.companyId!==companyId||!record(raw.source)||!record(raw.valuation))throw Error('מזהה חברה או מבנה מחקר לא תקין');
 const s=raw.source,v=raw.valuation;
 if(typeof s.filename!=='string'||!/^[a-zA-Z0-9_.-]+\.pdf$/.test(s.filename)||typeof s.sha256!=='string'||!/^[0-9a-f]{64}$/.test(s.sha256)||!validDate(s.asOf)||!['unverified','primary-verified'].includes(String(s.verification))||!Array.isArray(s.sourceUrls)||s.sourceUrls.length>30||!s.sourceUrls.every(safeSource))throw Error('מטא-נתוני מקור לא תקינים');
 if(!['USD','ILS','ILA'].includes(String(v.currency))||!['share','ADS'].includes(String(v.shareUnit))||!record(v.horizon)||!validDate(v.horizon.date)||typeof v.horizon.earningsPeriod!=='string'||!v.horizon.earningsPeriod.trim()||typeof v.horizon.note!=='string'||v.horizon.note.length>1500)throw Error('אופק, מטבע או יחידות אינם תקינים');
 if(v.reference!==null&&(!record(v.reference)||!finite(v.reference.value)||!validDate(v.reference.asOf)))throw Error('מחיר ייחוס לא תקין');
 if(v.declaredWeighted!==null&&!finite(v.declaredWeighted))throw Error('שווי משוקלל לא תקין');
 if(!Array.isArray(v.scenarios)||v.scenarios.length!==3||new Set(v.scenarios.map((x:unknown)=>record(x)?x.id:null)).size!==3||!['bear','base','bull'].every(id=>v.scenarios.some((x:unknown)=>record(x)&&x.id===id)))throw Error('דרושים שלושה תרחישים שונים');
 for(const x of v.scenarios){if(!record(x)||!finite(x.probability)||x.probability>100||!finite(x.statedPrice)||typeof x.rationale!=='string'||!x.rationale.trim()||x.rationale.length>2000)throw Error('הנחות תרחיש אינן תקינות');}
 if(Math.abs(v.scenarios.reduce((a:number,x:{probability:number})=>a+x.probability,0)-100)>1e-8)throw Error('הסתברויות חייבות להסתכם ל-100%');
 return raw as unknown as ResearchCandidate;
}
/** Pure preview; does not modify either snapshot or browser state. */
export function previewResearchCandidate(active:ResearchCandidate|null,candidate:ResearchCandidate):CandidateDiff[]{
 if(active&&active.companyId!==candidate.companyId)throw Error('אין להשוות בין חברות שונות');
 const diffs:CandidateDiff[]=[];
 const compare=(path:string,a:unknown,b:unknown)=>{if(JSON.stringify(a)!==JSON.stringify(b))diffs.push({path,before:a??null,after:b??null});};
 compare('source',active?.source??null,candidate.source);
 compare('valuation.currency',active?.valuation.currency??null,candidate.valuation.currency);
 compare('valuation.shareUnit',active?.valuation.shareUnit??null,candidate.valuation.shareUnit);
 compare('valuation.reference',active?.valuation.reference??null,candidate.valuation.reference);
 compare('valuation.horizon',active?.valuation.horizon??null,candidate.valuation.horizon);
 compare('valuation.declaredWeighted',active?.valuation.declaredWeighted??null,candidate.valuation.declaredWeighted);
 for(const id of ['bear','base','bull'])compare('valuation.scenarios.'+id,active?.valuation.scenarios.find(s=>s.id===id)??null,candidate.valuation.scenarios.find(s=>s.id===id)!);
 return diffs;
}
