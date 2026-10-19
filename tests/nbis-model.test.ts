import {it,expect} from 'vitest';
import {nbisModel,nbisFacts as f,capitalShares,originalNotes,maturityClaims,dilutedValue,modelYears} from '../src/research/nbisModel';
const base=f.scenarios[1];
it('includes pre-funded warrants, awards and August exchange once, without treasury shares',()=>{
 expect(capitalShares).toBeCloseTo(321.695845,6);
 expect(originalNotes).toBe(13450);
 expect(maturityClaims).toBeCloseTo(15756.875);
 expect(f.notes.filter(n=>n.id.startsWith('jun')).reduce((s,n)=>s+n.original,0)).toBe(200);
});
it('closes financing, fees and cash while pricing equity dilution from gross proceeds',()=>{
 const r=nbisModel(base)!;
 expect(r.opening).toBeCloseTo(8042.1+5680+775);
 expect(r.beforeFunding).toBeCloseTo(-2502.9);
 expect(r.gap).toBeCloseTo(5502.9);
 expect((r.newDebt+r.newEquity)*0.98).toBeCloseTo(r.gap);
 expect(r.cash).toBeCloseTo(3000);
 expect(r.fundingShares).toBeCloseTo(r.newEquity/160);
 expect(nbisModel({...base,issuePrice:80})!.fundingShares).toBeCloseTo(2*r.fundingShares);
 expect(nbisModel({...base,issuePrice:80})!.present).toBeLessThan(r.present);
});
it('does not create financing when existing sources exceed the cash reserve',()=>{
 const r=nbisModel({...base,capexH2:0,capex2027:0})!;
 expect(r.gap).toBe(0);expect(r.fundingShares).toBe(0);expect(r.cash).toBeGreaterThan(3000);
});
it('treats conversion as replacing the same claim, with economic threshold consistency',()=>{
 const note={id:'test',original:100,claim:120,rate:100}; // 10m shares; threshold $12
 const a=dilutedValue(300,0,10,[note]);expect(a.price).toBe(15);expect(a.debt).toBe(0);expect(a.shares).toBe(20);
 const b=dilutedValue(200,0,10,[note]);expect(b.price).toBe(8);expect(b.debt).toBe(120);expect(b.converted).toHaveLength(0);
 for(const s of f.scenarios){const r=nbisModel(s)!;for(const n of f.notes){const threshold=n.claim/(n.original*n.rate/1000);expect(r.diluted.converted.includes(n.id)?r.diluted.price>=threshold-1e-8:r.diluted.price<=threshold+1e-8).toBe(true);}}
});
it('required multiple reproduces reference price after dilution and discounting',()=>{
 const r=nbisModel(base)!;const priced=nbisModel({...base,multiple:r.requiredMultiple!})!;
 expect(priced.present).toBeCloseTo(f.referencePrice,6);
 expect(modelYears).toBeGreaterThan(1.19);expect(modelYears).toBeLessThan(1.21);
});
it('invalid or missing values suppress outputs, while operating cash can be negative',()=>{
 for(const update of [{issuePrice:0},{loanDraw:776},{margin:101},{operatingCash:NaN},{newAwards:-1},{capex2027:Infinity},{debtShare:101}])expect(nbisModel({...base,...update})).toBeNull();
 expect(nbisModel({...base,operatingCash:-1000})).not.toBeNull();
 expect(nbisModel({...base,revenue:0})!.requiredMultiple).toBeNull();
});
