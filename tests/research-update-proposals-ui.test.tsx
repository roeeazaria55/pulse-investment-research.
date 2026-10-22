// @vitest-environment jsdom
import {afterEach,describe,it,expect,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {ResearchUpdateProposal} from '../src/components/ResearchUpdateProposal';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const result={version:1,proposals:[{
 id:'research-proposal:one',companyId:'us-dlo-nasdaq-a',status:'review-only',period:'2026-Q2',
 sourceUrl:'https://rss.globenewswire.com/news-release/test',reportPublishedDate:'2026-08-13',
 evidence:[{observationId:'observation:one',metricId:'revenue',value:399.7,unit:'USD million',
 raw:'399.7',periodStart:'2026-04-01',periodEnd:'2026-06-30',
 basis:'IFRS rounded',sourceUrl:'https://rss.globenewswire.com/news-release/test',
 approvalStatus:'needs-reconciliation',forecastComparisonStatus:'blocked',
 reviewQuestion:'בדוק נתונים והגדרות'}],
 thesisImpact:'לא נקבע — נדרשת בדיקה',valuationAction:'אין שינוי במחירי יעד',
 aiAnalysisEnabled:false,missing:['אישור מקור וגרסה'],
}]};
describe('read-only research briefs',()=>{
 it('displays source facts and never labels an unapproved metric as approved',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>result}));
  render(<ResearchUpdateProposal companyId="us-dlo-nasdaq-a"/>);
  expect(await screen.findByText(/399.7 USD million/)).toBeTruthy();
  expect(screen.getByText(/לא אושר/)).toBeTruthy();
  expect(screen.getByText(/אינו ניתוח AI/)).toBeTruthy();
  expect(screen.getByText('אין שינוי במחירי יעד')).toBeTruthy();
 });
 it('does not show DLO report on the NBIS page',()=>{
  vi.stubGlobal('fetch',vi.fn());
  render(<ResearchUpdateProposal companyId="candidate-nebius"/>);
  expect(screen.queryByRole('region',{name:'הצעת עדכון מחקר מבוססת מקורות'})).toBeNull();
 });
});
