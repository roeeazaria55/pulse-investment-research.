import {describe,it,expect} from 'vitest';
import {buildEvidenceInsights,type EvidenceMetric} from '../src/research/evidenceInsights';
const metric:EvidenceMetric={
 id:'revenue',label:'הכנסות',value:120,previousValue:100,
 periodStart:'2026-04-01',periodEnd:'2026-06-30',
 previousPeriodStart:'2025-04-01',previousPeriodEnd:'2025-06-30',
 unit:'USD million',reviewStatus:'pending-review',
 sourceUrl:'https://www.sec.gov/example'
};
describe('Evidence insights fail closed',()=>{
 it('computes only arithmetic from compatible source periods',()=>{
  expect(buildEvidenceInsights([metric],'pending-review')).toMatchObject([
   {metricId:'revenue',difference:20,changePercent:20,kind:'calculation',
    reviewStatus:'pending-review',thesisStatus:'requires-analyst-review'}
  ]);
 });
 it('blocks unreconciled DLO and absent/unsupported comparisons',()=>{
  expect(buildEvidenceInsights([metric],'needs-reconciliation')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,previousValue:null}],'pending-review')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,previousPeriodStart:'2025-01-01'}],'pending-review')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,previousPeriodEnd:'2026-06-30'}],'pending-review')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,reviewStatus:'needs-reconciliation'}],'pending-review')).toEqual([]);
 });
 it('avoids misleading percentages on negative baselines and percentages',()=>{
  expect(buildEvidenceInsights([{...metric,value:10,previousValue:-20}],'pending-review')[0].changePercent).toBeNull();
  expect(buildEvidenceInsights([{...metric,id:'grossProfit',value:-5}],'pending-review')[0].changePercent).toBeNull();
  expect(buildEvidenceInsights([{...metric,id:'revenue',unit:'percent'}],'pending-review')[0].changePercent).toBeNull();
  expect(buildEvidenceInsights([{...metric,previousValue:0}],'pending-review')[0].changePercent).toBeNull();
 });
 it('compares balance dates and rejects mixed balance/flow windows',()=>{
  expect(buildEvidenceInsights([{...metric,id:'cash',periodStart:'2026-06-30',previousPeriodStart:'2025-06-30',previousPeriodEnd:'2025-06-30'}],'pending-review')).toHaveLength(1);
  expect(buildEvidenceInsights([{...metric,id:'cash',periodStart:'2026-06-30'}],'pending-review')).toEqual([]);
 });
 it('never produces a finding for missing date/source or unsupported metric',()=>{
  expect(buildEvidenceInsights([{...metric,previousPeriodEnd:undefined}],'pending-review')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,sourceUrl:'http://evil.test'}],'pending-review')).toEqual([]);
  expect(buildEvidenceInsights([{...metric,id:'unspecified'}],'pending-review')).toEqual([]);
 });
});
