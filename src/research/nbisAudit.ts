import facts from '../data/nbis-valuation.json';
export const auditShares=facts.sharesJune+facts.prefundedShares+facts.exchangeShares+facts.unvestedRsus+facts.options;
export type AuditInputs={cash:number;seniorDebt:number;extraShares:number;noncore:number;accretion:number;revenue:number;margin:number};
// Reverse valuation only: no implied forecast or automatic legal conversion.
export function requiredEnterprise(target:number,x:AuditInputs){
 if(!Number.isFinite(target)||target<0||Object.values(x).some(v=>!Number.isFinite(v)||v<0||v>1e7)||x.margin>100||x.accretion>100)return null;
 const shares=auditShares+x.extraShares;
 const notes=facts.notes.reduce((s,n)=>s+Math.max(n.original+(n.claim-n.original)*x.accretion/100,target*n.original*n.rate/1000),0);
 const enterprise=target*shares+x.seniorDebt+notes-x.cash-x.noncore;
 const ebitda=x.revenue*x.margin/100;
 return {shares,notes,enterprise,multiple:ebitda>0?enterprise/ebitda:null};
}
