// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,waitFor,fireEvent} from '@testing-library/react';
import raw from '../public/data/report-intake.json';
import {parseReportIntake,type ReportIntakeSnapshot} from '../src/data/reportIntake';
import {reportComparison} from '../src/research/reportComparison';
import {metricComparison,thesisMonitorFor} from '../src/research/thesisMonitoring';
import {ThesisMonitor} from '../src/components/ThesisMonitor';
const company='us-smci-nasdaq-common';
const metric=thesisMonitorFor(company)!.metrics[0];
const snapshot=()=>parseReportIntake(structuredClone(raw));
function future(){const data=snapshot();const d=data.documents.find(d=>d.companyId===company&&d.facts.length)!;d.facts=[{...d.facts.find(f=>f.concept.includes('revenue'))!,start:'2026-07-01',end:'2027-06-30',value:70e9}];data.documents=[d];return data;}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('maps actual issuer facts without turning historical revenue into a forecast-period miss',()=>{
 const result=reportComparison(snapshot(),company,metric);
 expect(result.status).toBe('mapped');expect(result.observation!.point).toMatchObject({value:39.063072,period:'FY2026',unit:'USD billion',basis:'revenue'});
 expect(metricComparison(result.observation!.point,metric.target).status).toBe('period');
 expect(result.observation!.document.sha256).toHaveLength(64);
});
it('compares exact future-period facts and preserves the research baseline and target',()=>{
 const before=JSON.stringify(metric),data=future(),r=reportComparison(data,company,metric);
 expect(metricComparison(r.observation!.point,metric.target)).toMatchObject({status:'comparable',difference:2});
 expect(JSON.stringify(metric)).toBe(before);
});
it('rejects year-to-date, quarterly, instant and wrong-currency facts for a fiscal annual forecast',()=>{
 for(const change of [{start:'2027-01-01'},{start:'2026-07-01',end:'2026-09-30'},{start:null},{unit:'iso4217:ILS'}]){
  const data=future();Object.assign(data.documents[0].facts[0],change);
  expect(reportComparison(data,company,metric).status).toBe('missing');
 }
});
it('blocks conflicting duplicates rather than silently choosing a filing',()=>{
 const data=future();data.documents[0].facts.push({...data.documents[0].facts[0],value:71e9,context:'different'});
 expect(reportComparison(data,company,metric).status).toBe('conflict');
 data.documents[0].facts[1].value=70e9;expect(reportComparison(data,company,metric).status).toBe('mapped');
});
it('blocks revised and stale-after-failure documents before comparison',()=>{
 for(const change of [{revised:true},{error:'Refresh failed'}]){
  const data=future();Object.assign(data.documents[0],change);expect(reportComparison(data,company,metric).status).toBe('review');
 }
});
it('never maps another issuer or a GAAP EPS fact into a normalized EPS forecast',()=>{
 const data=future();data.documents[0].companyId='candidate-sandisk';
 expect(reportComparison(data,company,metric).status).toBe('missing');
 const sndk=thesisMonitorFor('candidate-sandisk')!.metrics.find(m=>m.id==='earnings')!;
 expect(reportComparison(data,'candidate-sandisk',sndk).status).toBe('unsupported');
});
it('exposes explicit coverage states for every monitored company',()=>{
 for(const id of ['candidate-nebius','candidate-sandisk','us-dlo-nasdaq-a','candidate-brainsway',company]){
  for(const m of thesisMonitorFor(id)!.metrics)expect(reportComparison(snapshot(),id,m).label.length).toBeGreaterThan(0);
 }
});
it('renders an evidence-linked provisional gap without changing the source research',async()=>{
 const data:ReportIntakeSnapshot=future();vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
 render(<ThesisMonitor companyId={company}/>);
 await waitFor(()=>expect(screen.getByText('השוואה באותה תקופה והגדרה')).toBeTruthy());
 fireEvent.click(screen.getByText('הכנסות מוכרות'));
 expect(screen.getByText(/פער אוטומטי מההנחה · ממתין לאימות/)).toBeTruthy();
 expect(screen.getByRole('link',{name:'למקור הרשמי ↗'}).getAttribute('href')).toBe(data.documents[0].finalUrl);
 expect(screen.getByText(/FY2026: \$39.1B/)).toBeTruthy();
});
