// @vitest-environment jsdom
import {afterEach,describe,it,expect} from 'vitest';
import {cleanup,render,screen,within} from '@testing-library/react';
import nbisSource from '../public/data/nbis-q2-2026-source.json';
import dloSource from '../public/data/dlo-q2-2026-source.json';
import {nbisQ22026,extractNbisQ22026,nbisPulseForecasts} from '../src/research/nbisQ22026';
import {dloQ22026,extractDloQ22026,dloPulseForecasts} from '../src/research/dloQ22026';
import {compareFinancialForecast} from '../src/research/financialResults';
import {CompanyFinancialResults} from '../src/components/CompanyFinancialResults';
afterEach(cleanup);

describe('NBIS and DLO Q2 2026 checked issuer evidence',()=>{
 it('extracts four genuine three-month NBIS source cells without YTD conversions',()=>{
  expect(nbisQ22026.issues).toEqual([]);
  expect(nbisQ22026.observations.map(o=>[o.id,o.point.value])).toEqual([
   ['revenue',582.3],['profit',-175.9],['cashflow',2246.1],['capex',5657.4],
  ]);
  expect(nbisQ22026.observations.every(o=>o.periodStart==='2026-04-01'&&o.periodEnd==='2026-06-30')).toBe(true);
  expect(nbisQ22026.observations.every(o=>o.verification.endsWith('pending-review'))).toBe(true);
  expect(nbisQ22026.observations[2].sourceValues[0].raw).toBe('2,246.1');
  expect(nbisQ22026.observations[3].definition).toContain('נכסים בלתי מוחשיים');
 });
 it('extracts DLO rounded KPIs separately from thousands-denominated investing outlays',()=>{
  expect(dloQ22026.issues).toEqual([]);
  expect(dloQ22026.observations.map(o=>[o.id,o.point.value])).toEqual([
   ['revenue',399.7],['grossProfit',127.2],['profit',64.2],['capex',9.91],
  ]);
  expect(dloQ22026.observations[3].sourceUnit).toBe('USD thousands');
  expect(dloQ22026.observations[3].sourceValues[0].raw).toBe('(9,910)');
  expect(dloQ22026.observations[0].definition).toContain('עיגול');
 });
 it('rejects issuer identity, stale source, changed statement period and changed accounting units',()=>{
  expect(extractNbisQ22026({...nbisSource,companyId:'us-dlo-nasdaq-a'}).observations).toEqual([]);
  expect(extractDloQ22026({...dloSource,sourceUrl:'https://untrusted.example'}).observations).toEqual([]);
  const badPeriod=structuredClone(nbisSource);badPeriod.tables[0].periodStart='January 1, 2026';
  expect(extractNbisQ22026(badPeriod).observations.map(o=>o.id)).toEqual(['cashflow','capex']);
  const badUnit=structuredClone(dloSource);badUnit.tables[1].unit='USD million';
  expect(extractDloQ22026(badUnit).observations.some(o=>o.id==='capex')).toBe(false);
 });
 it('blocks post-publication forecasts and definition/period mismatches',()=>{
  for(const [observations,forecasts] of [[nbisQ22026.observations,nbisPulseForecasts()],[dloQ22026.observations,dloPulseForecasts()]] as const){
   for(const o of observations){
    const actual=compareFinancialForecast(o,forecasts[o.id]);
    expect(actual.result.status).not.toBe('comparable');
    const demo={companyId:o.companyId,point:{...o.point,value:o.point.value-1},description:'Synthetic target',definition:o.definition,asOf:o.resultsPublishedDate};
    expect(compareFinancialForecast(o,demo).result.status).toBe('timing');
    expect(compareFinancialForecast(o,{...demo,asOf:'2026-01-01',point:{...o.point,period:'FY2027'}}).result.status).not.toBe('comparable');
   }
  }
 });
 it('renders two new company panels through the shared FinancialResults cards',()=>{
  render(<CompanyFinancialResults companyId="candidate-nebius"/>);
  const nbis=within(screen.getByRole('region',{name:'נתוני בסיס NBIS Q2 2026 מהדוח הרשמי'}));
  expect(nbis.getByText('$582.3M')).toBeTruthy();
  expect(nbis.getByText('$5,657.4M')).toBeTruthy();
  expect(nbis.getAllByRole('link',{name:/מקור רשמי/})).toHaveLength(4);
  cleanup();
  render(<CompanyFinancialResults companyId="us-dlo-nasdaq-a"/>);
  const dlo=within(screen.getByRole('region',{name:'נתוני בסיס DLO Q2 2026 מהדוח הרשמי'}));
  expect(dlo.getByText('$399.7M')).toBeTruthy();
  expect(dlo.getByText('$9.91M')).toBeTruthy();
  expect(dlo.getAllByText('אין השוואה מספרית תקפה')).toHaveLength(4);
  expect(screen.queryByText(/פער מול התחזית/)).toBeNull();
 });
});
