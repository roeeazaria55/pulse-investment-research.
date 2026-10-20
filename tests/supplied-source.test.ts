import {it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {suppliedResearch,suppliedValue} from '../src/data/suppliedResearch';
it('retains the exact original PDFs and all financial tables by section',()=>{
 for(const r of suppliedResearch){
  const bytes=readFileSync(new URL('../public/research/'+r.filename,import.meta.url));
  expect(bytes.subarray(0,4).toString()).toBe('%PDF');
  expect(createHash('sha256').update(bytes).digest('hex')).toBe(r.sha256);
  expect(r.pages).toBe(5);expect(r.sections).toHaveLength(r.ticker==='NBIS'?12:13);
  expect(r.scenarios.map(s=>s.weight)).toEqual([20,50,30]);
 }
 expect(suppliedValue(suppliedResearch[0])).toBeCloseTo(182.333333333);
 const stress=suppliedResearch[1].sections[11].blocks.find(b=>b.type==='table')!;
 expect(stress.type==='table'&&stress.rows.map(row=>row[3])).toEqual(['$1,320','$855','$520']);
});
