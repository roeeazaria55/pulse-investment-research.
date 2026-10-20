import {it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {suppliedResearch,suppliedValue} from '../src/data/suppliedResearch';
it('retains the exact original PDFs and all financial tables by section',()=>{
 for(const r of suppliedResearch){
  const bytes=readFileSync(new URL('../public/research/'+r.filename,import.meta.url));
  expect(bytes.subarray(0,4).toString()).toBe('%PDF');
  expect(createHash('sha256').update(bytes).digest('hex')).toBe(r.sha256);
  expect(r.pages).toBe(({NBIS:5,SNDK:5,DLO:4,BWAY:3,SMCI:5} as Record<string,number>)[r.ticker]);expect(r.sections).toHaveLength(({NBIS:12,SNDK:13,DLO:10,BWAY:16,SMCI:14} as Record<string,number>)[r.ticker]);
  expect(r.scenarios.map(s=>s.weight)).toEqual([20,50,30]);
 }
 expect(suppliedValue(suppliedResearch[0])).toBeCloseTo(182.333333333);
 const stress=suppliedResearch[1].sections[11].blocks.find(b=>b.type==='table')!;
 expect(stress.type==='table'&&stress.rows.map(row=>row[3])).toEqual(['$1,320','$855','$520']);
});
