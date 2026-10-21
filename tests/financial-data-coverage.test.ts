import {describe,expect,it} from 'vitest';
import {financialDataCoverage,financialCoverageTotals} from '../src/research/financialDataCoverage';
import {thesisMonitors} from '../src/research/thesisMonitoring';

describe('Phase 1 financial data coverage inventory',()=>{
 it('does not silently imply all monitored companies have verified actuals',()=>{
  const all=financialDataCoverage();
  expect(all.length).toBe(thesisMonitors.length);
  expect(all.map(c=>c.companyId)).toEqual(thesisMonitors.map(c=>c.companyId));
  expect(all.every(c=>c.mapped<=c.tracked&&c.unmapped.length===c.tracked-c.mapped)).toBe(true);
  expect(financialCoverageTotals().issuerVerifiedMetrics).toBe(0);
 });
 it('distinguishes implemented semantic mappings from merely tracked indicators',()=>{
  const all=financialDataCoverage();
  expect(all.find(c=>c.companyId==='us-smci-nasdaq-common')?.mapped).toBe(2);
  expect(all.find(c=>c.companyId==='candidate-brainsway')?.mapped).toBe(2);
  expect(all.find(c=>c.companyId==='candidate-nebius')?.status).toBe('mapping-missing');
 });
});
