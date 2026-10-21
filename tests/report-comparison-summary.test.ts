import {describe,expect,it} from 'vitest';
import {summarizeReportComparisons} from '../src/research/reportComparisonSummary';
import type {ReportIntakeSnapshot} from '../src/data/reportIntake';
import type {ThesisMetric} from '../src/research/thesisMonitoring';

const snapshot={documents:[],sources:[]} as unknown as ReportIntakeSnapshot;
const metric=(id:string,target:ThesisMetric['target']):ThesisMetric=>({
 id,title:id,section:1,targetSection:1,baseline:'',observed:null,
 expectation:'',target,why:'',nextCheck:'',thesisRisk:'',
});
describe('read-only report comparison summary',()=>{
 it('never invents a measured surprise when official source facts are absent',()=>{
  const result=summarizeReportComparisons(snapshot,'us-smci-nasdaq-common',[
   metric('revenue',{value:10,unit:'USD billion',period:'Q2 2026',basis:'revenue'}),
   metric('cashflow',{value:2,unit:'USD billion',period:'Q2 2026',basis:'operating cash flow'}),
  ]);
  expect(result.total).toBe(2);
  expect(result.comparable).toBe(0);
  expect(result.waiting).toBe(2);
  expect(result.needsReview).toBe(0);
  expect(result.entries.every(e=>e.difference===null&&e.percent===null)).toBe(true);
 });
 it('marks unmapped metrics unsupported instead of deriving figures from unrelated facts',()=>{
  const result=summarizeReportComparisons(snapshot,'candidate-iren',[
   metric('gpu-utilization',{value:80,unit:'percent',period:'Q2 2026',basis:'utilization'}),
  ]);
  expect(result.entries[0].status).toBe('unsupported');
  expect(result.entries[0].difference).toBeNull();
 });
 it('returns an empty summary for no metrics',()=>{
  expect(summarizeReportComparisons(snapshot,'candidate-iren',[])).toEqual({
   total:0,comparable:0,needsReview:0,waiting:0,entries:[],
  });
 });
});
