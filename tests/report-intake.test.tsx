// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor,within} from '@testing-library/react';
import {parseReportIntake} from '../src/data/reportIntake';
import {ReportIntake} from '../src/components/ReportIntake';
import raw from '../public/data/report-intake.json';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('validates actual extracted official content with explicit review state and no implicit research update',()=>{
 const data=parseReportIntake(raw);expect(data.documents.length).toBeGreaterThan(0);
 for(const d of data.documents){expect(d.reviewStatus).toBe('pending-review');expect(d.sha256).toHaveLength(64);}
});
it('rejects unsafe/cross-issuer links, invented review approval and invalid structured periods',()=>{
 for(const mutate of [(x:any)=>x.documents[0].finalUrl='https://evil.test/report.pdf',(x:any)=>x.documents[0].companyId='us-smci-nasdaq-common',(x:any)=>x.documents[0].reviewStatus='approved',(x:any)=>x.documents[0].sha256='wrong',(x:any)=>x.documents[0].facts=[{concept:'us-gaap:Revenues',value:1,unit:'USD',start:'2026-07-01',end:'2026-06-30',context:'annual',status:'structured-source',definition:'source'}]]){
  const data=structuredClone(raw);mutate(data);expect(()=>parseReportIntake(data)).toThrow();
 }
});
it('shows read scope and source evidence and keeps data pending rather than claiming an automatic thesis change',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>raw}));
 const d=raw.documents.find(d=>d.tables.length)!;render(<ReportIntake companyId={d.companyId}/>);
 await waitFor(()=>expect(screen.getByText(/מסמכים נקראו/)).toBeTruthy());
 fireEvent.click(screen.getByText(/קליטת דוחות אוטומטית/));
 expect(screen.getByText(/המחקר ומחיר השווי אינם משתנים אוטומטית/)).toBeTruthy();
 fireEvent.click(screen.getByText(d.title));expect(screen.getAllByRole('link',{name:'פתיחת הדיווח הרשמי ↗'}).some(a=>a.getAttribute('href')===d.finalUrl)).toBe(true);
 fireEvent.click(within(screen.getByText(d.title).closest('details')!).getByText('שורות מטבלאות המקור · לבדיקת תקופה ויחידות'));expect(screen.getAllByRole('table').length).toBeGreaterThan(0);
});
it('reports unavailable intake as unavailable, rather than no new reports',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('offline')));render(<ReportIntake companyId="candidate-nebius"/>);
 fireEvent.click(screen.getByText('קליטת דוחות אוטומטית'));
 await waitFor(()=>expect(screen.getByText('מצב הקליטה אינו זמין. אין להסיק מכך שלא פורסם דוח.')).toBeTruthy());
});
