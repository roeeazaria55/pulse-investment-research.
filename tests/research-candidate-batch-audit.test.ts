import { describe, expect, it } from 'vitest';
import candidates from '../src/data/newResearchScenarioCandidates.json';
import { auditSourceValuation } from '../src/research/sourceValuationAudit';

type ScenarioId = 'bear' | 'base' | 'bull';
const known = new Set(['LMND', 'META', 'FTAI', 'IREN', 'NXSN', 'ENLT', 'Gilat Telecom']);

describe('Phase 0 candidate batch safety gate', () => {
  it('keeps all seven research records explicitly unverified and unpromoted', () => {
    expect(candidates.version).toBe(1);
    expect(candidates.status).toBe('research_unverified');
    expect(candidates.promoted).toBe(false);
    expect(candidates.companies).toHaveLength(7);
    expect(new Set(candidates.companies.map(c => c.ticker))).toEqual(known);
    expect(new Set(candidates.companies.map(c => c.companyId)).size).toBe(7);
  });

  it.each(candidates.companies)('$ticker has valid weighted scenarios and explicit valuation context', company => {
    expect(company.asOf).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(company.horizon).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(['USD', 'ILS', 'ILA']).toContain(company.currency);
    expect(company.basis.trim().length).toBeGreaterThan(10);
    expect(company.flags.length).toBeGreaterThan(0);
    const audit = auditSourceValuation(
      company.scenarios.map(s => ({ id: s.id as ScenarioId, weight: s.weight, price: s.price })),
      company.declared,
      company.tolerance,
    );
    expect(audit.status).not.toBe('invalid');
    expect(audit.calculated).not.toBeNull();
    expect(audit.status).toBe(company.check);
  });

  it('retains FTAI arithmetic discrepancy as a blocking review item', () => {
    const ftai = candidates.companies.find(c => c.ticker === 'FTAI')!;
    expect(ftai.check).toBe('discrepancy');
    expect(ftai.flags.some(flag => /weighted target mismatch/i.test(flag))).toBe(true);
    const audit = auditSourceValuation(
      ftai.scenarios.map(s => ({ id: s.id as ScenarioId, weight: s.weight, price: s.price })),
      ftai.declared,
      ftai.tolerance,
    );
    expect(audit.calculated).toBeCloseTo(163.67, 2);
    expect(audit.declared).toBe(164.1);
    expect(audit.status).toBe('discrepancy');
  });

  it('does not treat corrected Next Vision historicals as a reapproved forecast', () => {
    const next = candidates.companies.find(c => c.ticker === 'NXSN')!;
    expect(next.flags.some(flag => /forecasts require recalibration/i.test(flag))).toBe(true);
    expect(next.currency).toBe('ILS');
  });

  it('preserves agorot units for Gilat Telecom and company-specific probabilities', () => {
    const gilat = candidates.companies.find(c => c.ticker === 'Gilat Telecom')!;
    expect(gilat.currency).toBe('ILA');
    const distributions = new Set(candidates.companies.map(c => c.scenarios.map(s => s.weight).join('/')));
    expect(distributions.size).toBeGreaterThan(1);
  });
});
