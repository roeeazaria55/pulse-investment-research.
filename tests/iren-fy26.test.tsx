// @vitest-environment jsdom
import {afterEach,describe,expect,it,vi} from 'vitest';
import {cleanup,render,screen,within} from '@testing-library/react';
import source from '../public/data/iren-fy26-source.json';
import intake from '../public/data/report-intake.json';
import model from '../src/data/models/iren.json';
import {compareIrenForecast,extractIrenFy26,irenFy26,irenPulseForecasts} from '../src/research/irenFy26';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {IrenFinancialResults} from '../src/components/IrenFinancialResults';
import {blankResearch} from '../src/data/initial';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

describe('IREN FY26 checked issuer extract',()=>{
 it('extracts annual source values and keeps CAPEX components and its transformation explicit',()=>{
  expect(irenFy26.issues).toEqual([]);
  expect(irenFy26.observations.map(o=>[o.id,o.point.value])).toEqual([['revenue',707],['cashflow',2100.4],['capex',4333.1]]);
  for(const observation of irenFy26.observations){
   expect(observation.point).toMatchObject({period:'FY2026',unit:'USD million'});
   expect(observation.sourceUrl).toBe(source.sourceUrl);
   expect(observation.verification).toContain('pending-review');
  }
  const capex=irenFy26.observations[2];
  expect(capex.sourceValues.map(v=>v.raw)).toEqual(['(2,998.0)','(1,335.1)']);
  expect(capex.sourceValues.map(v=>v.value)).toEqual([-2998,-1335.1]);
  expect(capex.verification).toBe('derived-source-checked-pending-review');
 });
 it.each(['companyId','sourceUrl','pdfUrl','reviewStatus'])('rejects a mismatched or missing source attribute: %s',key=>{
  const x=structuredClone(source);(x as Record<string,unknown>)[key]='wrong';
  expect(extractIrenFy26(x).observations).toEqual([]);
 });
 it.each([{unit:'USD billion'},{periodKind:'Quarter ended'},{periodEnd:'June 30, 2025'}])('blocks a changed unit or period rather than annualizing or scaling silently: %j',change=>{
  const x=structuredClone(source);Object.assign(x.tables[0],change);
  const result=extractIrenFy26(x);
  expect(result.observations.some(o=>o.id==='revenue')).toBe(false);
  expect(result.issues.some(i=>i.id==='revenue')).toBe(true);
 });
 it('blocks conflicting annual values while retaining unrelated metrics',()=>{
  const x=structuredClone(source);x.tables[0].rows.push({...x.tables[0].rows[0],current:'999.0'});
  const result=extractIrenFy26(x);
  expect(result.observations.map(o=>o.id)).toEqual(['cashflow','capex']);
  expect(result.issues[0].reason).toContain('סותרים');
 });
 it('does not turn a missing CAPEX component into zero or use the investing subtotal',()=>{
  const x=structuredClone(source);x.tables[1].rows=x.tables[1].rows.filter(r=>r.label!=='Payments for computer hardware');
  const result=extractIrenFy26(x);
  expect(result.observations.some(o=>o.id==='capex')).toBe(false);
  expect(result.issues[0].reason).toContain('סעיף מקור חסר');
 });
 it('reads existing PULSE assumptions unchanged and blocks all actual FY26 gaps for precise reasons',()=>{
  const before=JSON.stringify(model),forecasts=irenPulseForecasts();
  expect(forecasts.revenue.point.value).toBe(4500);
  expect(forecasts.cashflow.point.value).toBe(1400);
  expect(forecasts.capex.point.value).toBe(17000);
  for(const observation of irenFy26.observations){
   const comparison=compareIrenForecast(observation,forecasts[observation.id]);
   expect(comparison.result.status).toBe('timing');
   expect('difference' in comparison.result).toBe(false);
   expect(comparison.reasons[0]).toContain('נתון בסיס');
   expect(comparison.reasons.some(r=>r.includes('תקופות שונות'))).toBe(true);
   if(observation.id!=='revenue')expect(comparison.reasons.some(r=>r.includes('הגדרות שונות'))).toBe(true);
  }
  expect(JSON.stringify(model)).toBe(before);
 });
 it('uses the shared comparison only for equal period, unit and basis',()=>{
  const observation=irenFy26.observations[0];
  // A synthetic target exercises the gate; it is not added to the PULSE model.
  const forecast={point:{...observation.point,value:700},description:'Synthetic FY26 test target',definition:observation.definition,asOf:'2026-08-26'};
  expect(compareIrenForecast(observation,forecast).result).toMatchObject({status:'comparable',difference:7,percent:1});
  expect(compareIrenForecast(observation,{...forecast,point:{...forecast.point,basis:'ARR'}}).result.status).toBe('definition');
  expect(compareIrenForecast(observation,{...forecast,point:{...forecast.point,unit:'USD billion'}}).result.status).toBe('definition');
 });
 it.each(['2026-10-20','2026-08-27',''])('never reports a surprise for a forecast after/on publication or with unknown timing: %s',asOf=>{
  const observation=irenFy26.observations[0];
  const forecast={point:{...observation.point,value:700},description:'Synthetic post-publication target',definition:observation.definition,asOf};
  const comparison=compareIrenForecast(observation,forecast);
  expect(comparison.result.status).toBe('timing');
  expect('difference' in comparison.result).toBe(false);
 });
 it('renders real values with source and blocked comparisons in the IREN company research page',()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>intake}));
  const changed=vi.fn();
  render(<ResearchExchange company={{id:'candidate-iren',name:'IREN',label:'IREN'}} current={blankResearch()} onChange={changed} onPrepare={()=>{}}/>);
  const section=within(screen.getByRole('region',{name:'נתוני בסיס IREN FY2026 מהדוח הרשמי'}));
  expect(section.getByText(/אינם הפתעה ואינם בדיקת איכות התחזית/)).toBeTruthy();
  expect(section.getByText('$707.0M')).toBeTruthy();
  expect(section.getByText('$2,100.4M')).toBeTruthy();
  expect(section.getByText('$4,333.1M')).toBeTruthy();
  expect(section.getAllByText('אין השוואה מספרית תקפה')).toHaveLength(3);
  expect(section.getAllByText(/שנה שהסתיימה ב־30.06.2026/)).toHaveLength(3);
  expect(section.getAllByRole('link',{name:/מקור רשמי/})[0].getAttribute('href')).toBe(source.pdfUrl+'#page=12');
  expect(section.queryByText(/פער מול התחזית/)).toBeNull();
  expect(changed).not.toHaveBeenCalled();
 });
 it('keeps the IREN-specific adapter off other company pages',()=>{
  render(<IrenFinancialResults companyId="candidate-nebius"/>);
  expect(screen.queryByRole('region')).toBeNull();
 });
});
