import {expect,it} from 'vitest';
import {auditSourceValuation} from '../src/research/sourceValuationAudit';
const scenarios=(bear:number,base:number,bull:number,weights:[number,number,number])=>[
  {id:'bear' as const,price:bear,weight:weights[0]},
  {id:'base' as const,price:base,weight:weights[1]},
  {id:'bull' as const,price:bull,weight:weights[2]},
];
it('flags the FTAI rounded-source discrepancy without replacing the source',()=>{
 const r=auditSourceValuation(scenarios(75.5,174.4,269.1,[30,50,20]),164.1);
 expect(r.status).toBe('discrepancy');expect(r.calculated).toBeCloseTo(163.67);expect(r.declared).toBe(164.1);
});
it('reconciles dynamic company-specific weights and supports separate source rounding',()=>{
 const lmnd=auditSourceValuation(scenarios(29.88,60.24,113.58,[30,45,25]),64.46);
 expect(lmnd.status).toBe('consistent');expect(lmnd.calculated).toBeCloseTo(64.455);
 expect(auditSourceValuation(scenarios(90.7,215.8,340.3,[25,55,20]),209.43).status).toBe('consistent');
 expect(auditSourceValuation(scenarios(125,245,419,[25,55,20]),249.8).status).toBe('consistent');
 expect(auditSourceValuation(scenarios(11.5,41.1,80.7,[35,45,20]),38.7,0.05).status).toBe('consistent');
});
it('rejects duplicate, missing and non-100-percent weights',()=>{
 expect(auditSourceValuation(scenarios(1,2,3,[20,50,20]),2).status).toBe('invalid');
 expect(auditSourceValuation(scenarios(1,2,3,[20,50,30]).map(s=>({...s,id:'bear' as const})),2).status).toBe('invalid');
 expect(auditSourceValuation(scenarios(1,2,NaN,[20,50,30]),2).status).toBe('invalid');
});
