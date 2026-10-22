// @vitest-environment jsdom
import {afterEach,describe,it,expect,vi} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import {AutomaticFinancialObservations} from '../src/components/AutomaticFinancialObservations';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const row={
 id:'observation:source-hash',companyId:'us-dlo-nasdaq-a',metricId:'operatingCash',
 sourceRaw:'140,522',sourceRow:'Net cash (used in ) / generated from operating activities',
 sourceTable:'Adjusted Free Cash Flow reconciliation',
 sourceUrl:'https://rss.globenewswire.com/news-release/2026/08/13/3344936/0/en/dlocal-reports-second-quarter-2026-financial-results.html',
 sourceSha256:'a'.repeat(64),reviewVersionId:'review:source',
 value:140.522,unit:'USD million',sourceUnit:'USD thousands',
 period:'2026-Q2',periodStart:'2026-04-01',periodEnd:'2026-06-30',
 basis:'IFRS cash from operations as cited in reconciliation',
 collectedAt:'2026-10-22T10:00:00Z',publishedDate:'2026-08-13',
 reviewStatus:'needs-reconciliation',revisedSource:true,
};
describe('issuer-collected accounting proposals',()=>{
 it('renders a source-linked pending metric without claiming an approved forecast surprise',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({version:1,source:'public/data/report-intake.json',observations:[row],issues:[]})}));
  render(<AutomaticFinancialObservations companyId="us-dlo-nasdaq-a"/>);
  expect(await screen.findByText(/140.522 USD million/)).toBeTruthy();
  expect(screen.getByText(/נדרש בירור: מסמך המקור השתנה/)).toBeTruthy();
  expect(screen.getByText(/אין השוואת תחזית לפני אישור/)).toBeTruthy();
  expect(screen.getByRole('link',{name:/צפייה בדוח הרשמי/}).getAttribute('href')).toBe(row.sourceUrl);
 });
 it('honestly reports that generated data is unavailable',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('offline')));
  render(<AutomaticFinancialObservations companyId="us-dlo-nasdaq-a"/>);
  await waitFor(()=>expect(screen.getByRole('status').textContent).toContain('אינו זמין'));
 });
 it('does not show DLO data in a different company',()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({version:1,observations:[row],issues:[]})}));
  render(<AutomaticFinancialObservations companyId="candidate-nebius"/>);
  expect(screen.queryByRole('region',{name:'נתונים שנקלטו אוטומטית לבדיקת אנליסט'})).toBeNull();
 });
});
