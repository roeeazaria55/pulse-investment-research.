import {describe,it,expect} from 'vitest';
import {validateCandidateStore} from '../src/components/EarningsResearchCandidates';
const cid='us-meta-nasdaq-a';
const url='https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx';
const draft={
 id:'earnings-candidate:'+'a'.repeat(32),companyId:cid,ticker:'META',
 sourceUrl:url,sourceSha256:'a'.repeat(64),reportPeriod:'Q3 2026',
 publishedDate:'2026-10-21',firstCandidateAt:'2026-10-28T20:00:00Z',
 status:'needs-review',publicationStatus:'not-approved',modelChange:'none',
 aiAnalysisExecuted:false,scenarioReview:{status:'not-calculated',bear:null,base:null,bull:null},
 metrics:[{id:'revenue',label:'הכנסות',value:64601,unit:'USD million',
 periodStart:'2026-07-01',periodEnd:'2026-09-30',
 previousValue:51242,absoluteChange:13359,percentChange:26.07,
 comparisonStatus:'historical-arithmetic-review-only',sourceUrl:url,
 sourceSha256:'a'.repeat(64),reviewStatus:'pending-review'}],
 analystReviewQuestions:[]
};
describe('source-bound earnings draft UI validation',()=>{
 it('shows pending META and never authorizes research changes',()=>{
  const rows=validateCandidateStore({version:1,candidates:[draft],latestByCompany:{[cid]:draft.id}},cid);
  expect(rows).toHaveLength(1);
  expect(rows[0].metrics[0].value).toBe(64601);
 });
 it('rejects forged sources, fake approvals and inconsistent digest',()=>{
  const wrap=(row:unknown)=>({version:1,candidates:[row],latestByCompany:{[cid]:draft.id}});
  expect(()=>validateCandidateStore(wrap({...draft,sourceUrl:'https://evil.example/data'}),cid)).toThrow();
  expect(()=>validateCandidateStore(wrap({...draft,publicationStatus:'approved'}),cid)).toThrow();
  expect(()=>validateCandidateStore(wrap({...draft,modelChange:'automatic'}),cid)).toThrow();
  expect(()=>validateCandidateStore(wrap({...draft,metrics:[{...draft.metrics[0],sourceSha256:'b'.repeat(64)}]}),cid)).toThrow();
 });
 it('rejects dangling current draft pointer and duplicate IDs',()=>{
  expect(()=>validateCandidateStore({version:1,candidates:[draft],latestByCompany:{[cid]:'earnings-candidate:'+'f'.repeat(32)}},cid)).toThrow();
  expect(()=>validateCandidateStore({version:1,candidates:[draft,draft],latestByCompany:{[cid]:draft.id}},cid)).toThrow();
 });
});
