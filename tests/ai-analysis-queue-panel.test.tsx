import {describe,it,expect} from 'vitest';
import {validateAIQueueStore} from '../src/components/AIAnalysisQueuePanel';
const id='us-meta-nasdaq-a',jid='ai-job:'+'a'.repeat(32);
const job={
 id:jid,candidateId:'earnings-candidate:'+'b'.repeat(32),companyId:id,ticker:'META',
 sourceUrl:'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx',
 sourceSha256:'c'.repeat(64),candidatePayloadSha256:'d'.repeat(64),reportPeriod:'Q3 2026',
 createdAt:'2026-10-29T00:00:00Z',updatedAt:'2026-10-29T00:00:00Z',
 status:'queued',statusReason:'verified-source-candidate-awaits-ai',
 attempts:0,analysisExecuted:false,publicationStatus:'not-approved',approvedModelChange:false,
 history:[{status:'queued',at:'2026-10-29T00:00:00Z'}]
};
const feed=(j:any=job)=>({version:1,jobs:[j],latestByCompany:{[id]:jid}});
describe('Source-to-AI queue presentation',()=>{
 it('does not mistake an unrun queued item for an AI analysis',()=>{
  expect(validateAIQueueStore(feed()).jobs[0].analysisExecuted).toBe(false);
 });
 it('rejects forged source links, unknown statuses, approval attempts and dangling references',()=>{
  expect(()=>validateAIQueueStore(feed({...job,sourceUrl:'https://investor.atmeta.com.evil.test/'}))).toThrow();
  expect(()=>validateAIQueueStore(feed({...job,status:'unverified-new-state'}))).toThrow();
  expect(()=>validateAIQueueStore(feed({...job,approvedModelChange:true}))).toThrow();
  expect(()=>validateAIQueueStore(feed({...job,publicationStatus:'approved'}))).toThrow();
  expect(()=>validateAIQueueStore({...feed(),latestByCompany:{[id]:'ai-job:'+'f'.repeat(32)}})).toThrow();
 });
});
