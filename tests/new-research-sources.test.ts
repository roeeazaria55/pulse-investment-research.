import {expect,it} from 'vitest';
import sources from '../src/data/newResearchSourceManifest.json';
import registry from '../src/data/researchIntakeRegistry.json';
it('attests all seven extracted uploaded sources without falsely declaring repository PDF ingestion',()=>{
 expect(sources.research).toHaveLength(7);
 expect(sources.storageStatus).toBe('external_import_bundle_only');
 for(const item of sources.research){
  const intake=registry.companies.find(x=>x.companyId===item.companyId);
  expect(intake?.filename).toBe(item.filename);
  expect(intake?.status).toBe('awaiting-byte-import');
  expect(item.sha256).toMatch(/^[0-9a-f]{64}$/);
  expect(item.bytes).toBeGreaterThan(40000);
  expect(item.pages).toBeGreaterThanOrEqual(3);
 }
});
