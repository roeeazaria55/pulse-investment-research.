import facts from '../data/nbis-valuation.json';
export {facts as nbisFacts};
export type ModelInputs = {revenue:number;margin:number;multiple:number;capexH2:number;capex2027:number;operatingCash:number;netAdvances:number;minCash:number;debtShare:number;issuePrice:number;newAwards:number;loanDraw:number;discount:number};
export type Note = {id:string;original:number;claim:number;rate:number};
export const modelYears=(Date.parse(facts.horizon)-Date.parse(facts.asOf))/(365.25*86400000);
export const capitalShares=facts.sharesJune+facts.prefundedShares+facts.exchangeShares+facts.unvestedRsus+facts.options;
export const originalNotes=facts.notes.reduce((s,n)=>s+n.original,0);
export const maturityClaims=facts.notes.reduce((s,n)=>s+n.claim,0);
// Economic conversion stress, not a prediction of legally available conversion.
// Treat every note as the larger of its conservative claim or conversion value.
export function dilutedValue(assets:number,seniorDebt:number,shares:number,notes:Note[]){
 let debt=seniorDebt+notes.reduce((s,n)=>s+n.claim,0), diluted=shares;
 const converted:string[]=[];
 for(const n of [...notes].sort((a,b)=>a.claim/(a.original*a.rate)-b.claim/(b.original*b.rate))){
  const extra=n.original*n.rate/1000;
  if((assets-debt)/diluted>n.claim/extra){debt-=n.claim;diluted+=extra;converted.push(n.id);}
 }
 return {price:Math.max(0,(assets-debt)/diluted),debt,shares:diluted,converted};
}
export function nbisModel(x:ModelInputs){
 const keys:(keyof ModelInputs)[]=['revenue','margin','multiple','capexH2','capex2027','operatingCash','netAdvances','minCash','debtShare','issuePrice','newAwards','loanDraw','discount'];
 if(keys.some(k=>!Number.isFinite(x[k])||Math.abs(x[k])>1e7||(k!=='operatingCash'&&k!=='netAdvances'&&x[k]<0))||x.margin>100||x.debtShare>100||x.discount>100||x.multiple>100||x.issuePrice<0.000001||x.loanDraw>facts.julyFacility)return null;
 const opening=facts.cashJune+facts.augustNetProceeds+x.loanDraw;
 const beforeFunding=opening+x.operatingCash+x.netAdvances-x.capexH2-x.capex2027;
 const gap=Math.max(0,x.minCash-beforeFunding);
 // A 2% underwriting cost assumption applies to both sources of new financing.
 const newDebt=gap*x.debtShare/100/0.98;
 const newEquity=gap*(1-x.debtShare/100)/0.98;
 const fundingShares=newEquity/x.issuePrice;
 const shares=capitalShares+x.newAwards+fundingShares;
 const cash=beforeFunding+(newDebt+newEquity)*0.98;
 const enterprise=x.revenue*x.margin/100*x.multiple;
 const seniorDebt=x.loanDraw+newDebt;
 const debtOnly= Math.max(0,(enterprise+cash-seniorDebt-maturityClaims)/shares);
 const diluted=dilutedValue(enterprise+cash,seniorDebt,shares,facts.notes);
 const factor=(1+x.discount/100)**modelYears;
 const futureReference=facts.referencePrice*factor;
 const requiredEnterprise=futureReference*shares+seniorDebt+facts.notes.reduce((s,n)=>s+Math.max(n.claim,futureReference*n.original*n.rate/1000),0)-cash;
 const ebitda=x.revenue*x.margin/100;
 const requiredRatio=ebitda>0?requiredEnterprise/ebitda:NaN;
 const requiredMultiple=Number.isFinite(requiredRatio)?requiredRatio:null;
 return {opening,beforeFunding,gap,newDebt,newEquity,fundingShares,shares,cash,enterprise,seniorDebt,debtOnly,diluted,present:diluted.price/factor,requiredMultiple,upside:(diluted.price/factor/facts.referencePrice-1)*100};
}
