import {describe,it,expect} from 'vitest';
import {classifyResearchAlert,unreadResearchAlerts} from '../src/research/alertPolicy';
import type {News} from '../src/types';
const official={
 id:'sec:1:2',ticker:'META',company:'Meta',headline:'Quarterly results',sourceUrl:'https://www.sec.gov/test',
 collectedAt:'2026-10-28T07:00:00Z',publishedAt:'2026-10-28T06:00:00Z',importance:'high' as const,
 summary:'',demo:false,rating:{
 version:'evidence-3.2',eventKind:'results',eventLabel:'דוחות',eventScore:85,potentialMateriality:85,
 level:'high' as const,sourceAuthority:'official-verified',sourceReliability:'verified',
 companyRelevance:'direct' as const,confidence:'high' as const,basis:'official-metadata' as const,
 verifiedOfficial:true,independentConfirmations:0,why:'metadata',evidenceUrls:['https://www.sec.gov/test']
 }} satisfies News;
describe('Research alert policy',()=>{
 it('caps high severity and never infers critical from a headline',()=>{
  expect(classifyResearchAlert(official)?.severity).toBe('high');
  expect(classifyResearchAlert({...official,rating:{...official.rating,verifiedOfficial:false,basis:'headline-only'}})?.severity).toBe('low');
  expect(classifyResearchAlert({...official,rating:{...official.rating,eventScore:48,level:'medium'}})?.severity).toBe('medium');
 });
 it('respects unread state, deduplication and source evidence',()=>{
  expect(unreadResearchAlerts([official,official],[])).toHaveLength(1);
  const sibling={...official,id:'sec:1:3'};
  const groups=[{id:'event:results',itemIds:[official.id,sibling.id]}];
  expect(unreadResearchAlerts([official,sibling],[],5,groups)).toHaveLength(1);
  expect(unreadResearchAlerts([sibling],[official.id],5,groups)).toEqual([]);
  expect(unreadResearchAlerts([official],[official.id])).toEqual([]);
  expect(unreadResearchAlerts([{...official,demo:true}],[])).toEqual([]);
  expect(unreadResearchAlerts([{...official,sourceUrl:'http://bad'}],[])).toEqual([]);
  expect(unreadResearchAlerts([{...official,rating:{...official.rating,companyRelevance:'context'}}],[])).toEqual([]);
 });
});
