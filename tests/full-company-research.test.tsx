// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,within} from '@testing-library/react';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {FullCompanyResearch,hasFullResearch} from '../src/components/FullCompanyResearch';
import {publishedFor} from '../src/data/publishedResearch';
import {blankResearch} from '../src/data/initial';
import {researchFields} from '../src/types';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('includes every research field in the full reading, with recovered conversation and supplemental provenance',()=>{
 for(const id of ['candidate-nebius','candidate-sandisk']){
  const pack=publishedFor(id)!.analysis;render(<FullCompanyResearch analysis={pack}/>);
  for(const key of researchFields)expect(screen.getByText(pack.fields[key])).toBeTruthy();
  expect(screen.getAllByText(/התמליל המלא/).length).toBeGreaterThan(0);
  expect(screen.getByText(/מסגרת מעקב משלימה/)).toBeTruthy();
  expect(screen.getAllByRole('heading',{level:4})).toHaveLength(6);
  expect(screen.getAllByRole('link')).toHaveLength(pack.sourceUrls.length);
  cleanup();
 }
 expect(hasFullResearch('us-meta-nasdaq-a')).toBe(false);
});
it('opens NBIS and Sandisk full analysis by default without changing personal research',()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false}));
 for(const [id,label] of [['candidate-nebius','NBIS'],['candidate-sandisk','SNDK']]){
  const change=vi.fn();render(<ResearchExchange company={{id,name:label,label}} current={blankResearch()} onChange={change} onPrepare={()=>{}}/>);
  const details=screen.getByText('קריאת המחקר המלא').closest('details')!;
  expect(details.open).toBe(true);
  expect(within(details).getByRole('heading',{name:'1. ההסבר מהשיחות'})).toBeTruthy();
  expect(change).not.toHaveBeenCalled();cleanup();
 }
});
it('navigates chapters by focus without changing hash routing or resetting research',()=>{
 const scroll=vi.fn();HTMLElement.prototype.scrollIntoView=scroll;
 render(<FullCompanyResearch analysis={publishedFor('candidate-nebius')!.analysis}/>);
 fireEvent.click(screen.getByRole('button',{name:'התרחישים והתמחור'}));
 expect(document.activeElement).toBe(screen.getByRole('heading',{name:'4. התרחישים והתמחור'}));
 expect(location.hash).toBe('');expect(scroll).toHaveBeenCalled();
});
