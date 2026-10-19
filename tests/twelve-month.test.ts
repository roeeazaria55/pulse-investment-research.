import {it,expect} from 'vitest';
import model from '../src/data/nbis-12-month-model.json';
import {weightedTarget} from '../src/research/twelveMonth';
it('reconstructs the original weighted target without discounting or rolling the horizon',()=>{
 const r=weightedTarget(model.scenarios,model.referencePrice)!;
 expect(r.target).toBe(248.5);expect(r.upside).toBeCloseTo(33.595,2);
 expect(model.analysisDate).toBe('2026-10-15');expect(model.horizonDate).toBe('2027-10-15');
 expect( weightedTarget(model.scenarios,248.5)!.upside).toBe(0);
});
it('rejects inconsistent weights, missing inputs and unstable reference prices',()=>{
 expect(weightedTarget(model.scenarios.map((x,i)=>({...x,probability:i===0?30:x.probability})),186.01)).toBeNull();
 for(const ref of [0,NaN,Infinity,1e-320])expect(weightedTarget(model.scenarios,ref)).toBeNull();
 expect(weightedTarget([{target:NaN,probability:20},...model.scenarios.slice(1)],186.01)).toBeNull();
});
