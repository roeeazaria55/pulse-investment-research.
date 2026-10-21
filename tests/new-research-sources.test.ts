import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import sources from '../src/data/newResearchSourceManifest.json';
import registry from '../src/data/researchIntakeRegistry.json';
it('attests all seven extracted uploaded sources with explicit unverified status after PDF and page ingestion',()=>{
 expect(sources.research).toHaveLength(7);
 expect(sources.storageStatus).toBe('repository_pdfs_and_page_text');
 for(const item of sources.research){
  const intake=registry.companies.find(x=>x.companyId===item.companyId);
  expect(intake?.filename).toBe(item.filename);
  expect(intake?.status).toBe('repository-source-unverified');
  expect(item.sha256).toMatch(/^[0-9a-f]{64}$/);
  expect(item.bytes).toBeGreaterThan(40000);
  expect(item.pages).toBeGreaterThanOrEqual(3);
 }
});

it('preserves the seven actual original PDFs and all seven page JSON files',()=>{
 for(const item of sources.research){
  const bytes=readFileSync(new URL('../public/research/'+item.filename,import.meta.url));
  expect(bytes.subarray(0,4).toString()).toBe('%PDF');
  expect(bytes.length).toBe(item.bytes);
  expect(createHash('sha256').update(bytes).digest('hex')).toBe(item.sha256);
  const name=item.ticker==='Gilat Telecom'?'Gilat_Telecom':item.ticker;
  const pages=JSON.parse(readFileSync(new URL('../public/research-pages/'+name+'.pages.json',import.meta.url),'utf8')).pages;
  expect(pages).toHaveLength(item.pages);
  expect(pages.every((p:{page:number;text:string},i:number)=>p.page===i+1&&p.text.trim().length>0)).toBe(true);
 }
});

