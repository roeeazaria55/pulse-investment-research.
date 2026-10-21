// @vitest-environment jsdom
import {afterEach,describe,expect,it,vi} from 'vitest';
import {cleanup,render,screen,within,waitFor} from '@testing-library/react';
import smciSource from '../public/data/smci-fy26-source.json';
import irenSource from '../public/data/iren-fy26-source.json';
import intake from '../public/data/report-intake.json';
import {extractSmciFy26,smciFy26,smciPulseForecasts} from '../src/research/smciFy26';
import {extractIrenFy26,irenFy26} from '../src/research/irenFy26';
import {compareFinancialForecast,parseSourceNumber} from '../src/research/financialResults';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {CompanyFinancialResults} from '../src/components/CompanyFinancialResults';
import {ThesisMonitor} from '../src/components/ThesisMonitor';
import {blankResearch} from '../src/data/initial';
import {parseReportIntake} from '../src/data/reportIntake';
import {summarizeReportComparisons} from '../src/research/reportComparisonSummary';
import {thesisMonitorFor} from '../src/research/thesisMonitoring';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const company='us-smci-nasdaq-common';

describe('shared checked-source engine for IREN and SMCI',()=>{
 it('reads SMCI consolidated FY2026 GAAP statements and scales thousands to millions, retaining raw values and sign',()=>{
  expect(smciFy26.issues).toEqual([]);
  expect(smciFy26.observations.map(o=>[o.id,o.point.value])).toEqual([['revenue',39063.072],['profit',2770.486],['cashflow',-6809.886]]);
  expect(smciFy26.observations.map(o=>o.sourceValues[0].raw)).toEqual(['39,063,072','2,770,486','(6,809,886)']);
  for(const o of smciFy26.observations){
   expect(o).toMatchObject({companyId:company,periodStart:'2025-07-01',periodEnd:'2026-06-30',sourceUnit:'USD thousands',sourceUrl:smciSource.sourceUrl,documentUrl:smciSource.documentUrl,publishedDate:'2026-08-31',verification:'source-checked-pending-review'});
   expect(o.point).toMatchObject({unit:'USD million',period:'FY2026'});
   expect(o.locationUrl).toContain(smciSource.documentUrl+'#:~:text=');
  }
 });
 it('cross-checks the bounded SMCI cells with the retained non-dimensional official XBRL evidence',()=>{
  const doc=intake.documents.find(d=>d.id===smciSource.intakeEvidence.documentId)!;
  // Live CI refreshes may replace the intake version; the saved hash identifies only the original checked read.
  expect(smciSource.intakeEvidence.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(doc.finalUrl).toBe(smciSource.documentUrl);
  const concepts=['us-gaap:revenuefromcontractwithcustomerexcludingassessedtax','us-gaap:operatingincomeloss','us-gaap:netcashprovidedbyusedinoperatingactivities'];
  for(const [index,concept] of concepts.entries()){
   const o=smciFy26.observations[index];
   const facts=doc.facts.filter(f=>f.concept===concept&&f.start===o.periodStart&&f.end===o.periodEnd&&f.context===smciSource.intakeEvidence.context&&f.unit==='iso4217:USD');
   expect(facts.length).toBeGreaterThan(0);
   expect(facts.every(f=>f.value===o.point.value*1e6)).toBe(true);
  }
 });
 it('preserves IREN values, raw cells and derived CAPEX in the same engine',()=>{
  expect(irenFy26.issues).toEqual([]);
  expect(irenFy26.observations.map(o=>o.point.value)).toEqual([707,2100.4,4333.1]);
  expect(irenFy26.observations[2].sourceValues.map(v=>v.raw)).toEqual(['(2,998.0)','(1,335.1)']);
  expect(irenFy26.observations[2].verification).toBe('derived-source-checked-pending-review');
 });
 it.each([
  ['IREN',irenSource,extractIrenFy26],['SMCI',smciSource,extractSmciFy26],
 ] as const)('rejects unavailable sources and issuer mixups for %s',(name,source,extract)=>{
  expect(extract(null).observations).toEqual([]);
  expect(extract({}).issues[0].id).toBe('source');
  expect(extract({...source,companyId:'another-issuer'}).observations).toEqual([]);
  expect(extract({...source,revised:true}).observations).toEqual([]);
  expect(extract({...source,checkedDate:'2026-01-01'}).observations).toEqual([]);
 });
 it.each(['sourceUrl','documentUrl','publishedDate','reviewStatus','resultsPublishedDate','resultsSourceUrl'])('rejects unverified SMCI identity metadata: %s',key=>{
  expect(extractSmciFy26({...smciSource,[key]:'wrong'}).observations).toEqual([]);
 });
 it.each([{unit:'USD million'},{periodKind:'Quarter ended'},{periodStart:'July 1, 2026'},{periodEnd:'June 30, 2025'},{page:60}])('blocks changed SMCI units, period or statement location: %j',change=>{
  const x=structuredClone(smciSource);Object.assign(x.tables[0],change);
  const result=extractSmciFy26(x);
  expect(result.observations.map(o=>o.id)).toEqual(['cashflow']);
  expect(result.issues.map(i=>i.id)).toEqual(['revenue','profit']);
 });
 it('blocks a missing operating cash flow and never substitutes investing cash flow',()=>{
  const x=structuredClone(smciSource);x.tables[1].rows=[{label:'Net cash used in investing activities',current:'(200,300)'}];
  const result=extractSmciFy26(x);
  expect(result.observations.map(o=>o.id)).toEqual(['revenue','profit']);
  expect(result.issues[0].reason).toContain('סעיף מקור חסר');
 });
 it('deduplicates identical cells, blocks conflicting values and refuses ambiguous duplicated tables',()=>{
  const x=structuredClone(smciSource);x.tables[0].rows.push({...x.tables[0].rows[0]});
  expect(extractSmciFy26(x).observations).toHaveLength(3);
  x.tables[0].rows[2].current='999';
  expect(extractSmciFy26(x).observations.map(o=>o.id)).toEqual(['profit','cashflow']);
  expect(extractSmciFy26(x).issues[0].reason).toContain('סותרים');
  x.tables.push(structuredClone(x.tables[1]));
  expect(extractSmciFy26(x).observations.map(o=>o.id)).toEqual(['profit']);
 });
 it.each(['','NaN','1,00','--','1e9','∞'])('does not silently coerce an unsupported numeric cell: %s',raw=>{
  expect(()=>parseSourceNumber(raw)).toThrow();
 });
 it('blocks later PULSE assumptions, preserves their units and does not invent profit or CFO targets',()=>{
  const forecasts=smciPulseForecasts();
  expect(forecasts.revenue!.point).toMatchObject({value:68,period:'FY2027',unit:'USD billion',basis:'revenue'});
  expect(forecasts.profit).toBeUndefined();expect(forecasts.cashflow).toBeUndefined();
  const comparison=compareFinancialForecast(smciFy26.observations[0],forecasts.revenue);
  expect(comparison.result.status).toBe('timing');
  expect('difference' in comparison.result).toBe(false);
  expect(comparison.reasons.some(r=>r.includes('תקופות שונות'))).toBe(true);
  expect(comparison.reasons.some(r=>r.includes('יחידות'))).toBe(true);
 });
 it('allows a synthetic pre-publication target only when period, unit and accounting basis match',()=>{
  const o=smciFy26.observations[0];
  const forecast={companyId:o.companyId,point:{...o.point,value:39000},description:'Synthetic FY2026 target',definition:o.definition,asOf:'2026-08-10'};
  expect(compareFinancialForecast(o,{...forecast,companyId:'candidate-iren'}).result.status).toBe('company');
  expect(compareFinancialForecast(o,forecast).result).toMatchObject({status:'comparable',difference:expect.closeTo(63.072,6)});
  for(const point of [{...forecast.point,period:'FY2027'},{...forecast.point,unit:'USD billion'},{...forecast.point,basis:'adjusted revenue'}])expect(compareFinancialForecast(o,{...forecast,point}).result.status).not.toBe('comparable');
  for(const asOf of ['2026-08-11','2026-08-30','2026-08-31','2026-10-20',''])expect(compareFinancialForecast(o,{...forecast,asOf}).result.status).toBe('timing');
 });
 it('renders source-backed SMCI metrics on its company research page using the same card structure as IREN',()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>intake}));
  const changed=vi.fn();
  render(<ResearchExchange company={{id:company,name:'Super Micro Computer',label:'SMCI'}} current={blankResearch()} onChange={changed} onPrepare={()=>{}}/>);
  const section=within(screen.getByRole('region',{name:'נתוני בסיס SMCI FY2026 מהדוח הרשמי'}));
  for(const value of ['$39,063.072M','$2,770.486M','$-6,809.886M'])expect(section.getByText(value)).toBeTruthy();
  expect(section.getAllByText('אין השוואה מספרית תקפה')).toHaveLength(3);
  expect(section.getAllByText(/ממתין לבדיקת אנליסט/)).toHaveLength(3);
  expect(section.getAllByRole('link',{name:/מקור רשמי/})).toHaveLength(3);
  expect(section.getByTestId('smci-fy26-revenue').className).toBe('thesis-metric');
  expect(section.queryByText(/פער מול התחזית/)).toBeNull();
  expect(changed).not.toHaveBeenCalled();
  cleanup();render(<CompanyFinancialResults companyId="candidate-iren"/>);
  expect(screen.getByTestId('iren-fy26-revenue').className).toBe('thesis-metric');
 });
 it.each([null,'2026-10-20','2026-08-31'])('blocks numeric surprises in the legacy SMCI monitor and its summary when publication timing is not valid: %s',async publishedDate=>{
  const data=parseReportIntake(structuredClone(intake));
  const d=data.documents.find(d=>d.companyId===company&&d.facts.length)!;
  d.error=null;d.revised=false;d.publishedDate=publishedDate;
  const fact=d.facts.find(f=>f.concept.includes('revenue'))!;
  d.facts=[{...fact,start:'2026-07-01',end:'2027-06-30',value:70e9}];data.documents=[d];
  const monitor=thesisMonitorFor(company)!;
  const summary=summarizeReportComparisons(data,company,monitor.metrics);
  expect(summary.entries.find(e=>e.metricId==='revenue')).toMatchObject({status:'timing',difference:null,percent:null});
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
  render(<ThesisMonitor companyId={company}/>);
  await waitFor(()=>expect(screen.getByText(/לא הוכח שהתחזית נקבעה לפני פרסום התוצאה/)).toBeTruthy());
  expect(screen.queryByText(/פער אוטומטי מההנחה/)).toBeNull();
 });
});
