import {describe,expect,it} from 'vitest';
import raw from '../public/data/report-intake.json';
import {parseReportIntake,type IntakeFact,type ReportIntakeSnapshot} from '../src/data/reportIntake';
import {financialMappingReadiness,pilotFinancialRequirements} from '../src/research/financialMappingReadiness';
import {reportComparison} from '../src/research/reportComparison';
import {summarizeReportComparisons} from '../src/research/reportComparisonSummary';
import {thesisMonitorFor,type ThesisMetric} from '../src/research/thesisMonitoring';

const nbis='candidate-nebius';
const metric=thesisMonitorFor(nbis)!.metrics[0];
const snapshot=()=>parseReportIntake(structuredClone(raw));
function tableOnly(){
 const data=snapshot();
 data.documents=data.documents.filter(d=>d.companyId===nbis).slice(0,1);
 data.documents[0].facts=[];data.documents[0].error=null;data.documents[0].revised=false;
 data.sources=[{companyId:nbis,lastAttemptAt:data.generatedAt,status:'ok',error:null}];
 return data;
}
const codes=(data:ReportIntakeSnapshot|null,id=nbis)=>financialMappingReadiness(data,id)!.gaps.map(g=>g.code);

describe('pilot financial evidence gates',()=>{
 it('keeps all three pilots visible even without an existing thesis monitor or intake source',()=>{
  for(const p of pilotFinancialRequirements){
   const readiness=financialMappingReadiness(snapshot(),p.companyId)!;
   expect(readiness.ticker).toBe(p.ticker);
   expect(readiness.semanticMappings).toBe(0);
   expect(readiness.gaps.some(g=>g.code==='mapping-review-required')).toBe(true);
  }
  expect(financialMappingReadiness(snapshot(),'candidate-iren')!.requirements.join(' ')).toContain('ביוני');
  expect(financialMappingReadiness(snapshot(),'unknown')).toBeUndefined();
 });
 it('distinguishes an unavailable snapshot from a successful snapshot without issuer reports',()=>{
  expect(codes(null)).toContain('snapshot-unavailable');
  expect(codes(null)).not.toContain('reports-missing');
  const data=snapshot();data.documents=[];data.sources=[];
  expect(codes(data,'candidate-iren')).toEqual(['intake-not-observed','reports-missing','mapping-review-required']);
  data.sources=[{companyId:nbis,lastAttemptAt:data.generatedAt,status:'no-candidates',error:null}];
  expect(codes(data)).toContain('source-incomplete');
  expect(codes(data)).not.toContain('intake-not-observed');
 });
 it('does not promote table cells or research baseline values into structured facts',()=>{
  const data=tableOnly();
  data.documents[0].tables=[{rows:[['USD million','2026'],['Revenue','3200']],spans:false,scope:'Unreviewed source rows',page:null}];
  data.documents[0].tableCount=1;
  expect(metric.observed).not.toBeNull();
  expect(financialMappingReadiness(data,nbis)!.structuredFacts).toBe(0);
  expect(codes(data)).toContain('structured-facts-missing');
  const result=reportComparison(data,nbis,metric);
  expect(result.status).toBe('unsupported');expect(result.observation).toBeUndefined();
  expect(result.label).toContain('עובדות מובנות');
 });
 it('counts only the requested issuer and discloses failed collection without discarding older evidence',()=>{
  const data=tableOnly();
  data.sources[0].status='failed';data.sources[0].error='HTTP 403';
  expect(codes(data)).toContain('source-incomplete');
  expect(financialMappingReadiness(data,nbis)!.documents).toHaveLength(1);
  expect(financialMappingReadiness(data,'candidate-iren')!.documents).toHaveLength(0);
  expect(financialMappingReadiness(data,'candidate-iren')!.structuredFacts).toBe(0);
 });
 it.each([{revised:true},{error:'Refresh failed'}])('makes source revisions and failed refreshes explicit: %j',change=>{
  const data=tableOnly();Object.assign(data.documents[0],change);
  expect(codes(data)).toContain('document-review-required');
  expect(reportComparison(data,nbis,metric).observation).toBeUndefined();
 });
 it('requires semantic review even when raw facts exist, and preserves conflicting source values',()=>{
  const data=tableOnly();
  const fact:IntakeFact={concept:'us-gaap:revenues',value:3200e6,unit:'iso4217:USD',start:'2026-01-01',end:'2026-12-31',context:'group',status:'structured-source',definition:'Source tag, unreviewed mapping'};
  data.documents[0].facts=[fact,{...fact,value:3300e6,context:'conflicting'}];
  const before=JSON.stringify(data);
  expect(financialMappingReadiness(data,nbis)!.structuredFacts).toBe(2);
  expect(codes(data)).not.toContain('structured-facts-missing');
  expect(codes(data)).toContain('mapping-review-required');
  expect(reportComparison(data,nbis,metric).status).toBe('unsupported');
  const summary=summarizeReportComparisons(data,nbis,[metric]);
  expect(summary.comparable).toBe(0);expect(summary.entries[0].difference).toBeNull();expect(summary.entries[0].percent).toBeNull();
  expect(JSON.stringify(data)).toBe(before);
 });
 it.each([
  {concept:'us-gaap:revenues',unit:'iso4217:USD',start:'2026-01-01',end:'2026-12-31'},
  {concept:'us-gaap:revenues',unit:'iso4217:EUR',start:'2026-01-01',end:'2026-12-31'},
  {concept:'us-gaap:revenues',unit:'iso4217:USD',start:'2026-01-01',end:'2026-06-30'},
  {concept:'nebius:ARR',unit:'iso4217:USD',start:null,end:'2026-12-31'},
 ])('never infers a pilot mapping from concept similarity or incompatible periods/units: %j',change=>{
  const data=tableOnly();
  data.documents[0].facts=[{value:3200e6,context:'test',status:'structured-source',definition:'Unreviewed',...change}];
  for(const pilot of pilotFinancialRequirements){
   const metrics:ThesisMetric[]=thesisMonitorFor(pilot.companyId)?.metrics??[metric];
   for(const m of metrics){
    const result=reportComparison(data,pilot.companyId,m);
    expect(result.status).toBe('unsupported');expect(result.observation).toBeUndefined();
   }
  }
 });
});
