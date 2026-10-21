import {expect,it} from 'vitest';
import candidates from '../src/data/newResearchScenarioCandidates.json';
import manifest from '../src/data/newResearchSourceManifest.json';
import {auditSourceValuation} from '../src/research/sourceValuationAudit';

it('matches each of seven source-grounded snapshots to an uploaded PDF manifest entry',()=>{
 expect(candidates.promoted).toBe(false);
 expect(candidates.companies).toHaveLength(7);
 expect(new Set(candidates.companies.map(c=>c.companyId)).size).toBe(7);
 for(const c of candidates.companies){
  expect(manifest.research.some(r=>r.companyId===c.companyId)).toBe(true);
  expect(c.scenarios.map(s=>s.id)).toEqual(['bear','base','bull']);
  const report=auditSourceValuation(c.scenarios.map(s=>({id:s.id as 'bear'|'base'|'bull',weight:s.weight,price:s.price})),c.declared,c.tolerance);
  expect(report.status).toBe(c.check);
  expect(c.flags.length).toBeGreaterThan(1);
 }
});
it('preserves the source FTAI discrepancy as a blocking audit issue',()=>{
 const c=candidates.companies.find(c=>c.ticker==='FTAI')!;
 const report=auditSourceValuation(c.scenarios.map(s=>({id:s.id as 'bear'|'base'|'bull',weight:s.weight,price:s.price})),c.declared,c.tolerance);
 expect(report.status).toBe('discrepancy');
 expect(report.calculated).toBeCloseTo(163.67,8);
 expect(report.declared).toBe(164.1);
});
it('keeps agorot and shekels distinct for Gilat and Next Vision',()=>{
 expect(candidates.companies.find(c=>c.ticker==='Gilat Telecom')?.currency).toBe('ILA');
 expect(candidates.companies.find(c=>c.ticker==='NXSN')?.currency).toBe('ILS');
});
