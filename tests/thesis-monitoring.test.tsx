// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {metricComparison,thesisMonitors,type MetricPoint} from '../src/research/thesisMonitoring';
import {ThesisMonitor,ValuationContext} from '../src/components/ThesisMonitor';
import {FullCompanyResearch} from '../src/components/FullCompanyResearch';
import {publishedFor} from '../src/data/publishedResearch';
import {suppliedFor} from '../src/data/suppliedResearch';
afterEach(cleanup);
const annual:MetricPoint={value:3200,period:'2026',unit:'USD million',basis:'group revenue'};
it('blocks partial-period and accounting-definition comparisons, and never interprets missing data as zero',()=>{
 expect(metricComparison({...annual,value:582.3,period:'Q2 2026'},annual).status).toBe('period');
 expect(metricComparison({...annual,basis:'ARR'},annual).status).toBe('definition');
 expect(metricComparison({...annual,unit:'USD billion'},annual).status).toBe('definition');
 expect(metricComparison(null,annual).status).toBe('missing');
 expect(metricComparison({...annual,value:NaN},annual).status).toBe('missing');
 expect(metricComparison(annual,null).status).toBe('qualitative');
 expect(metricComparison({...annual,value:0},annual)).toMatchObject({status:'comparable',difference:-3200,percent:-100});
 expect(metricComparison({...annual,value:3520},annual)).toMatchObject({status:'comparable',difference:320,percent:10});
 expect(metricComparison({...annual,value:1},{...annual,value:0})).toMatchObject({status:'comparable',difference:1,percent:null});
});
it('keeps the pilot source-bound, uses six business-specific metrics per company and exposes no false pass/fail score',()=>{
 for(const monitor of thesisMonitors){
  const report=suppliedFor(monitor.companyId)!;
  expect(monitor.asOf).toBe(report.date);expect(monitor.metrics).toHaveLength(6);
  for(const metric of monitor.metrics){
   expect(report.sections.some(s=>s.number===metric.section)).toBe(true);
   expect(report.sections.some(s=>s.number===metric.targetSection)).toBe(true);
   expect(metricComparison(metric.observed,metric.target).status).not.toBe('comparable');
  }
  render(<ThesisMonitor companyId={monitor.companyId}/>);
  const region=screen.getByRole('region',{name:`מעקב התזה של ${monitor.ticker}`});
  const rows=region.querySelectorAll('details');expect(rows).toHaveLength(6);
  expect(Array.from(rows).every(row=>!row.open)).toBe(true);
  expect(within(region).getByText(/נקודת הפתיחה והתחזית נשמרות מהמחקר שסופק/)).toBeTruthy();
  expect(within(region).getByRole('link',{name:`מקור מדדי המעקב · PDF ${monitor.ticker} ↗`}).getAttribute('href')).toContain(report.filename);
  expect(region.textContent).not.toContain('עומד לפי ההנחות');cleanup();
 }
});
it('jumps from a monitoring metric to the original chapter and opens a collapsed full analysis without changing routing',()=>{
 const id='candidate-nebius';const scroll=vi.fn();HTMLElement.prototype.scrollIntoView=scroll;
 render(<><ThesisMonitor companyId={id}/><details><summary>מחקר</summary><FullCompanyResearch analysis={publishedFor(id)!.analysis}/></details></>);
 const region=screen.getByRole('region',{name:'מעקב התזה של NBIS'});
 fireEvent.click(within(region).getByText('הכנסות מוכרות'));
 fireEvent.click(within(region).getAllByRole('button',{name:'לנתוני המקור · פרק 4'})[0]);
 const heading=screen.getByRole('heading',{name:'4. דוחות כספיים ורווחיות'});
 expect(heading.closest('details')!.open).toBe(true);expect(document.activeElement).toBe(heading);
 expect(scroll).toHaveBeenCalled();expect(location.hash).toBe('');
});
it('separates a dated document quote from a live price and identifies the missing Sandisk 12-month bridge',()=>{
 render(<ValuationContext companyId="candidate-sandisk"/>);
 const region=screen.getByRole('region',{name:'אופק והנחות השווי של SNDK'});
 expect(region.textContent).toContain('$1,371.12');expect(region.textContent).toContain('20.10.2026');
 expect(region.textContent).toContain('אינו שער חי');expect(region.textContent).toContain('FY2028');
 fireEvent.click(within(region).getByText('ההנחות שמניעות את השווי ומה חסר ליעד של 12 חודשים'));
 expect(within(region).getByText(/יעד ל־20.10.2027 טרם נבנה/)).toBeTruthy();
 cleanup();render(<ValuationContext companyId="candidate-nebius"/>);
 expect(screen.getByText('יעד ל־20.10.2027 · 12 חודשים מתאריך הניתוח')).toBeTruthy();
});
