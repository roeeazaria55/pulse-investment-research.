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

it('reconciles DLO quarterly forecasts to annual totals while retaining the source scenario prices',()=>{
 const r=suppliedResearch.find(r=>r.ticker==='DLO')!;
 const table=r.sections[3].blocks.find(b=>b.type==='table')!;
 if(table.type!=='table')throw Error('Missing source quarterly table');
 for(const start of [0,5,10])for(const column of [1,2,3])expect(table.rows.slice(start,start+4).reduce((sum,row)=>sum+Number(row[column]),0)).toBeCloseTo(Number(table.rows[start+4][column]),8);
 expect(suppliedValue(r)).toBeCloseTo(23.308,8);
});
