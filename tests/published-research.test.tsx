// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor} from '@testing-library/react';
import {publishedResearch,publishedFor,pendingResearchSources,researchAge} from '../src/data/publishedResearch';
import {officialRegistry,type OfficialItem} from '../src/data/official';
import {parseAnalysis,applyAnalysis} from '../src/research/exchange';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {ResearchBaselineStatus} from '../src/components/ResearchBaselineStatus';
import {blankResearch,initialState} from '../src/data/initial';
import {validState} from '../src/state/storage';
import {researchFields} from '../src/types';
import snapshot from '../public/data/official-sources.json';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('has exactly one complete validated dated baseline for each of the eleven identities',()=>{
 expect(publishedResearch).toHaveLength(11);
 for(const c of officialRegistry.companies){
  const p=publishedFor(c.id)!;expect(p).toBeTruthy();
  const a=parseAnalysis(JSON.stringify(p.analysis),c.id);
  expect(researchFields.every(k=>a.fields[k].length>20)).toBe(true);
  expect(a.sourceUrls.length).toBeGreaterThan(0);expect(a.missing.length).toBeGreaterThan(0);
  expect(p.period).toBeTruthy();expect(p.scope).toBeTruthy();
 }
 expect(publishedFor('GILT')).toBeUndefined();
});
it('every baseline adopts without erasing notes and survives state validation with previous fields',()=>{
 for(const {analysis} of publishedResearch){
  const prior={...blankResearch(),thesis:'Personal original',notes:[{id:'n',text:'Keep',createdAt:'2026-10-19T08:00:00Z'}]};
  const next=applyAnalysis(prior,analysis,[...researchFields]);
  expect(next.notes).toEqual(prior.notes);expect(next.versions![0].fields.thesis).toBe(prior.thesis);
  const state={...initialState(),research:{NBIS:next}};
  expect(validState(JSON.parse(JSON.stringify(state)))).toBe(true);
 }
});
it('never treats lastSeen/collection as publication and deduplicates matching URLs',()=>{
 const p=publishedFor('candidate-nebius')!.analysis;
 const ref={companyId:p.companyId,collectedAt:'2099-01-01T00:00:00Z',lastSeenAt:'2099-01-01T00:00:00Z'};
 const items=[
  {...ref,id:'read',url:p.sourceUrls[0].split('?')[0]+'?other=1',publishedDate:null},
  {...ref,id:'old',url:'https://nebius.com/newsroom/old',publishedDate:'2026-01-01'},
  {...ref,id:'unknown',url:'https://nebius.com/newsroom/unknown',publishedDate:null},
  {...ref,id:'duplicate',url:'https://nebius.com/newsroom/unknown?tracking=1',publishedDate:null},
  {...ref,id:'new',url:'https://nebius.com/newsroom/new',publishedDate:'2026-10-20'},
  {...ref,id:'other',companyId:'candidate-iren',url:'https://iren.com/new',publishedDate:'2026-10-20'},
 ] as OfficialItem[];
 expect(pendingResearchSources(p,items).map(x=>x.id)).toEqual(['old','unknown','new']);
 expect(researchAge(p.asOf,new Date('2027-01-20T00:00:00Z'))).toBeGreaterThan(90);
});
it('each company renders its own baseline and no render/preview changes personal research',()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false}));
 for(const c of officialRegistry.companies){
  const onChange=vi.fn();
  render(<ResearchExchange company={c} current={{...blankResearch(),thesis:'My original'}} onChange={onChange} onPrepare={()=>{}}/>);
  expect(screen.getByText('מחקר בסיס ל־'+c.label)).toBeTruthy();expect(onChange).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText('השוואת מחקר הבסיס למחקר שלי'));
  expect(screen.getByText('My original')).toBeTruthy();expect(onChange).not.toHaveBeenCalled();
  cleanup();
 }
});
it('failed status check keeps baseline status honest',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('offline')));
 render(<ResearchBaselineStatus pack={publishedFor('candidate-nebius')!.analysis}/>);
 await waitFor(()=>expect(screen.getByText(/מצב הפרסומים אינו זמין/)).toBeTruthy());
});
it('shows an unknown-date publication as unknown instead of newly published',async()=>{
 const base=snapshot.items.find(x=>x.companyId==='candidate-nebius')!;
 const data={...snapshot,items:[{...base,url:base.url+'-unreviewed',publishedDate:null,publishedDateBasis:'unknown',dateEvidenceUrl:null}]};
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
 render(<ResearchBaselineStatus pack={publishedFor('candidate-nebius')!.analysis}/>);
 await waitFor(()=>expect(screen.getByText('פרסומים לבדיקה שלא נכללו במחקר (1)')).toBeTruthy());
 expect(screen.getByText('תאריך פרסום לא ידוע — עשוי להיות מסמך קודם')).toBeTruthy();
});
