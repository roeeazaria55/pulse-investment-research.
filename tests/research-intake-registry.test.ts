import {expect,it} from 'vitest';
import registry from '../src/data/researchIntakeRegistry.json';
import official from '../public/data/official-registry.json';
it('tracks all 12 distinct identities and imported sources as unverified',()=>{
 expect(registry.companies).toHaveLength(12);
 expect(new Set(registry.companies.map(c=>c.companyId)).size).toBe(12);
 expect(new Set(registry.companies.map(c=>c.companyId))).toEqual(new Set(official.companies.map(c=>c.id)));
 for(const r of registry.companies){
  expect(r.filename).toMatch(/\.pdf$/);
  expect(['existing-source-recheck','repository-source-unverified']).toContain(r.status);
 }
});
it('retains superseding corrected PDFs for Next Vision and META',()=>{
 expect(registry.companies.find(x=>x.ticker==='META')?.filename).toMatch(/_FIXED\.pdf$/);
 expect(registry.companies.find(x=>x.ticker==='NXSN')?.filename).toMatch(/_FIXED\.pdf$/);
});
