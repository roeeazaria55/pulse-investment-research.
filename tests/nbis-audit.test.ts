import {it,expect} from 'vitest';
import {requiredEnterprise,auditShares} from '../src/research/nbisAudit';
import {dilutedValue} from '../src/research/nbisModel';
import facts from '../src/data/nbis-valuation.json';
const x={cash:3000,seniorDebt:5000,extraShares:20,noncore:1000,accretion:50,revenue:11000,margin:40};
it('reverse bridge reproduces each original target under economic conversion',()=>{
 for(const price of [115,235,360]){
 const r=requiredEnterprise(price,x)!;
 const notes=facts.notes.map(n=>({...n,claim:n.original+(n.claim-n.original)*.5}));
 expect(dilutedValue(r.enterprise+x.cash+x.noncore,x.seniorDebt,auditShares+x.extraShares,notes).price).toBeCloseTo(price,8);
 expect(r.multiple).toBeCloseTo(r.enterprise/4400);
 }
});
it('recognizes funding, private holdings and dilution without silently forecasting them',()=>{
 const r=requiredEnterprise(235,x)!;
 expect(requiredEnterprise(235,{...x,extraShares:21})!.enterprise-r.enterprise).toBeCloseTo(235);
 expect(requiredEnterprise(235,{...x,cash:4000})!.enterprise-r.enterprise).toBeCloseTo(-1000);
 expect(requiredEnterprise(235,{...x,revenue:0})!.multiple).toBeNull();
 for(const bad of [{cash:NaN},{margin:101},{accretion:-1},{extraShares:Infinity}])expect(requiredEnterprise(235,{...x,...bad})).toBeNull();
});
