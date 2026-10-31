import {describe,it,expect} from 'vitest';
import {modelReviewSignals,type ReviewBaseline} from '../src/research/modelReviewSignals';
import type {IntakeDocument} from '../src/data/reportIntake';
const baseline:ReviewBaseline={companyId:'company-a',ticker:'AAA',asOf:'2026-10-20',sourceUrls:[],horizon:'2027-10-20'};
const doc=(overrides:Partial<IntakeDocument>={}):IntakeDocument=>({companyId:'company-a',status:'extracted',publishedDate:'2026-10-29',url:'https://issuer.test/results',sha256:'a'.repeat(64),revised:false,revisions:[],...overrides} as IntakeDocument);
describe('model review reasons without automatic model changes',()=>{
 it('requires a dated, read, uncited issuer report newer than the research',()=>{
  expect(modelReviewSignals([baseline],[doc()],'2026-10-31')).toHaveLength(1);
  for(const row of [doc({companyId:'other'}),doc({publishedDate:null}),doc({publishedDate:'2026-08-01'}),doc({publishedDate:'2026-12-01'}),doc({status:'read-no-supported-data'}),doc({publishedDate:'2026-02-31'})])expect(modelReviewSignals([baseline],[row],'2026-10-31')).toEqual([]);
  expect(modelReviewSignals([{...baseline,sourceUrls:[doc().url]}],[doc()],'2026-10-31')).toEqual([]);
 });
 it('limits notices to one per company and reopens on a new source version',()=>{
  const notices=modelReviewSignals([baseline],[doc(),doc({publishedDate:'2026-10-30',sha256:'b'.repeat(64)})],'2026-10-31');
  expect(notices).toHaveLength(1);expect(notices[0].id).toContain('b'.repeat(64));
  expect(notices[0].id).not.toBe(modelReviewSignals([baseline],[doc()],'2026-10-31')[0].id);
 });
 it('flags a source revision only when the cited prior version was observed after baseline',()=>{
  const b={...baseline,sourceUrls:[doc().url]};
  const d=doc({publishedDate:'2026-08-01',revised:true,lastSuccessfulAt:'2026-10-30T08:00:00Z',revisions:[{sha256:'c'.repeat(64),firstDetectedAt:'2026-10-21T08:00:00Z',lastSuccessfulAt:'2026-10-29T08:00:00Z'}]});
  expect(modelReviewSignals([b],[d],'2026-10-31')[0].id).toContain('revision:');
  expect(modelReviewSignals([b],[{...d,revisions:[]}],'2026-10-31')).toEqual([]);
 });
 it('treats expired horizons as review signals without inventing a horizon',()=>{
  expect(modelReviewSignals([{...baseline,horizon:'2026-10-01'}],[],'2026-10-31')).toHaveLength(1);
  expect(modelReviewSignals([{...baseline,horizon:''}],[],'2026-10-31')).toEqual([]);
 });
});
