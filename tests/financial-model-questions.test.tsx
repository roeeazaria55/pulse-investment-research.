// @vitest-environment jsdom
// The model remains an immutable reference, never a financial actual.
import {it,expect} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {FinancialModelQuestions} from '../src/components/FinancialModelQuestions';
import {companyModelFor} from '../src/data/companyModels';
import {parseReportIntake} from '../src/data/reportIntake';
import intake from '../public/data/report-intake.json';
import type {ResearchMetric} from '../src/components/LatestResearchUpdate';
it('links an observed operating margin to existing META inputs without editing them',()=>{
 const before=JSON.stringify(companyModelFor('us-meta-nasdaq-a'));
 render(<FinancialModelQuestions companyId="us-meta-nasdaq-a" metrics={[{id:'operatingIncome',label:'רווח תפעולי'} as ResearchMetric]}/>);
 expect(screen.getByRole('region',{name:'השפעה אפשרית על הנחות המודל'}).textContent).toContain('36');
 expect(screen.getByText(/אין התאמת תחזית/)).toBeTruthy();
 expect(JSON.stringify(companyModelFor('us-meta-nasdaq-a'))).toBe(before);cleanup();
});
it('does not invent a quantitative model for SMCI',()=>{
 render(<FinancialModelQuestions companyId="us-smci-nasdaq-common" metrics={[{id:'inventory',label:'מלאי'} as ResearchMetric]}/>);
 expect(screen.getByText(/לא נמצא מודל כמותי תואם/)).toBeTruthy();cleanup();
});
it('accepts real SEC JSON but rejects another issuer, accession or format scope',()=>{
 expect(parseReportIntake(intake).documents.some(d=>d.format==='sec-json')).toBe(true);
 for(const field of ['companyId','secAccession','readScope']){
  const changed=structuredClone(intake);
  const d=changed.documents.find(d=>d.format==='sec-json')! as unknown as Record<string,unknown>;
  d[field]=field==='companyId'?'candidate-nebius':field==='readScope'?'full-body':'forged';
  expect(()=>parseReportIntake(changed)).toThrow('Invalid');
 }
});
