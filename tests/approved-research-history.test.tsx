import {describe,it,expect} from 'vitest';
import {validateApprovedResearchStore} from '../src/components/ApprovedResearchHistory';
const cid='us-meta-nasdaq-a',id='research-v:'+'a'.repeat(32);
const version={
 id,companyId:cid,ticker:'META',pdfPath:'public/approved-research/META/'+'a'.repeat(32)+'.pdf',
 pdfSha256:'b'.repeat(64),immutableSha256:'c'.repeat(64),
 sourcePacketSha256:'d'.repeat(64),parentVersionId:null,
 researchHeadline:'סקירת META לאחר אישור',publicationStatus:'approved-upon-protected-pr-merge'
};
const feed=(v:any=version)=>({version:1,versions:[v],activeByCompany:{[cid]:id}});
describe('owner-protected approved research archive UI',()=>{
 it('reads versioned PDFs with a matching active issuer pointer',()=>{
  expect(validateApprovedResearchStore(feed()).versions[0].id).toBe(id);
 });
 it('rejects unreviewed proposals, forged paths and dangling pointers',()=>{
  expect(()=>validateApprovedResearchStore(feed({...version,publicationStatus:'proposed-awaiting-authenticated-merge'}))).toThrow();
  expect(()=>validateApprovedResearchStore(feed({...version,pdfPath:'https://example.test/secret.pdf'}))).toThrow();
  expect(()=>validateApprovedResearchStore(feed({...version,pdfPath:'public/approved-research/META/../../secret.pdf'}))).toThrow();
  expect(()=>validateApprovedResearchStore({...feed(),activeByCompany:{[cid]:'research-v:'+'f'.repeat(32)}})).toThrow();
 });
});
