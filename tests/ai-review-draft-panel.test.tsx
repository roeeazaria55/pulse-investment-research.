import {describe,it,expect} from 'vitest';
import {validateAIReviewFeed} from '../src/components/AIReviewDraftPanel';

const cid='us-meta-nasdaq-a';
const item={
 id:'ai-draft:'+'a'.repeat(32),companyId:cid,ticker:'META',model:'gpt-6.1-sol',
 status:'requires-human-review',analysisMode:'model-generated-unverified',
 reviewStatus:'not-approved',publicationStatus:'not-approved',
 sourcePacketSha256:'b'.repeat(64),immutableSha256:'c'.repeat(64),
 firstRecordedAt:'2026-10-29T10:00:00Z',approvedTargetPrice:null,approvedScenarios:null,
 proposedValuationAction:'no-automatic-change',
 evidenceCitations:[{evidenceId:'observation:1',kind:'financial-observation',claim:'נתון מקור',uncertainty:'טעון בדיקה'}],
 analystQuestions:['בדוק מה מקור הנתון'],interpretations:[],suggestedScenarioReview:[]
};
describe('AI report draft visibility never means publication',()=>{
 it('permits review-only model output with source hashes',()=>{
  expect(validateAIReviewFeed({version:1,drafts:[item]},cid)).toHaveLength(1);
 });
 it('rejects self-promoted prices, approvals and probability totals',()=>{
  const show=(v:unknown)=>validateAIReviewFeed({version:1,drafts:[v]},cid);
  expect(()=>show({...item,publicationStatus:'approved'})).toThrow();
  expect(()=>show({...item,approvedTargetPrice:140})).toThrow();
  expect(()=>show({...item,model:'unknown-free-model'})).toThrow();
  expect(()=>show({...item,sourcePacketSha256:'bad'})).toThrow();
  expect(()=>show({...item,suggestedScenarioReview:[
   {id:'bear',suggestedProbability:20,reason:'risk',evidenceIds:[],status:'review-only'},
   {id:'base',suggestedProbability:60,reason:'base',evidenceIds:[],status:'review-only'},
   {id:'bull',suggestedProbability:30,reason:'bull',evidenceIds:[],status:'review-only'}
  ]})).toThrow();
 });
});
