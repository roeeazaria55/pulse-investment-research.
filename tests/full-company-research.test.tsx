// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {FullCompanyResearch,hasFullResearch} from '../src/components/FullCompanyResearch';
import {SuppliedValuation} from '../src/components/SuppliedResearch';
import {publishedFor} from '../src/data/publishedResearch';
import {suppliedResearch,suppliedValue,suppliedScenarioValue} from '../src/data/suppliedResearch';
import {companyModelFor} from '../src/data/companyModels';
import {researchTarget} from '../src/research/researchTarget';
import {blankResearch} from '../src/data/initial';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('includes all source-document sections, paragraphs, tables and source PDF links',()=>{
 for(const report of suppliedResearch){
  render(<FullCompanyResearch analysis={publishedFor(report.companyId)!.analysis}/>);
  expect(screen.getAllByRole('heading',{level:4})).toHaveLength(report.sections.length+1);
  expect(screen.queryAllByRole('table')).toHaveLength(({NBIS:6,SNDK:9,DLO:5,BWAY:0,SMCI:5} as Record<string,number>)[report.ticker]);
  for(const section of report.sections){
   expect(screen.getByRole('heading',{name:`${section.number}. ${section.title}`})).toBeTruthy();
   for(const block of section.blocks)if(block.type==='paragraph')expect(screen.getByText(block.text)).toBeTruthy();
  }
  expect(screen.getByRole('link',{name:`פתיחת PDF המקור · ${report.ticker} ↗`}).getAttribute('href')).toContain(report.filename);
  expect(screen.queryByText(/התמליל המלא/)).toBeNull();cleanup();
 }
 expect(hasFullResearch('us-meta-nasdaq-a')).toBe(false);
});
it('uses unrounded Nebius scenario arithmetic and keeps Sandisk FY2028 distinct from a 12-month target',()=>{
 const [nbis,sndk]=suppliedResearch;
 expect(suppliedScenarioValue(nbis,nbis.scenarios[1])).toBeCloseTo(156.6666667);
 expect(suppliedValue(nbis)).toBeCloseTo(182.3333333);
 expect(suppliedValue(nbis)).not.toBeCloseTo(60*.2+157*.5+307*.3);
 expect(suppliedValue(sndk)).toBe(1759.5);
 expect(researchTarget(sndk.companyId)!.horizon).toBe('');
 expect(researchTarget(sndk.companyId)!.horizonLabel).toContain('FY2028');
 render(<SuppliedValuation companyId={sndk.companyId}/>);
 expect(screen.getByTestId('supplied-weighted-target').textContent).toBe('$1,759.50');
 expect(screen.getAllByText(/לא יעד קשיח ל־12 חודשים/).length).toBeGreaterThan(0);
});
it('keeps full analysis collapsed until opened and preserves the active valuation',()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false}));
 for(const report of suppliedResearch){
  const change=vi.fn();const company={id:report.companyId,name:report.ticker,label:report.ticker};
  const current=blankResearch();const {rerender}=render(<ResearchExchange company={company} current={current} onChange={change} onPrepare={()=>{}}/>);
  expect(screen.getByText('קריאת המחקר המלא').closest('details')!.open).toBe(false);
  fireEvent.click(screen.getByText('קריאת המחקר המלא'));
  expect(screen.getByText('קריאת המחקר המלא').closest('details')!.open).toBe(true);
  expect(screen.getByRole('heading',{name:`1. ${report.sections[0].title}`})).toBeTruthy();
  rerender(<ResearchExchange company={company} view="valuation" current={current} onChange={change} onPrepare={()=>{}}/>);
  expect(screen.getByRole('region',{name:`מודל המסמך של ${report.ticker}`})).toBeTruthy();
  if(companyModelFor(report.companyId)){expect(screen.getByText('ארכיון מודלים קודמים · אינו הניתוח הפעיל').closest('details')!.open).toBe(false);
  expect(screen.getByRole('heading',{name:`${report.ticker} · מודל מחושב ל־12 חודשים`}).closest('details')!.open).toBe(false);}
  expect(change).not.toHaveBeenCalled();cleanup();
 }
});
it('navigates chapters by focus without changing hash routing',()=>{
 const scroll=vi.fn();HTMLElement.prototype.scrollIntoView=scroll;
 render(<FullCompanyResearch analysis={publishedFor('candidate-nebius')!.analysis}/>);
 fireEvent.click(screen.getByText('תוכן העניינים המלא'));
 fireEvent.click(screen.getByRole('button',{name:'10. הערכת שווי ל־12 חודשים — מכפיל הכנסות'}));
 expect(document.activeElement).toBe(screen.getByRole('heading',{name:'10. הערכת שווי ל־12 חודשים — מכפיל הכנסות'}));
 expect(location.hash).toBe('');expect(scroll).toHaveBeenCalled();
});
