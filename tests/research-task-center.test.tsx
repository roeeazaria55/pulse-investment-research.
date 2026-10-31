// @vitest-environment jsdom
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor,within} from '@testing-library/react';
import {ResearchTaskCenter} from '../src/components/ResearchTaskCenter';
import {prioritizeTasks,type ResearchTask} from '../src/research/researchTasks';
import intake from '../public/data/report-intake.json';
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();});
const draft=(i:number)=>({id:'ai-draft:'+String(i).repeat(32),companyId:['candidate-nebius','us-meta-nasdaq-a','us-smci-nasdaq-common','candidate-sandisk'][i-1],ticker:['NBIS','META','SMCI','SNDK'][i-1],model:'gpt-6.1-sol',status:'requires-human-review',analysisMode:'model-generated-unverified',reviewStatus:'not-approved',publicationStatus:'not-approved',sourcePacketSha256:'b'.repeat(64),immutableSha256:'c'.repeat(64),firstRecordedAt:'2026-10-30T10:00:00Z',approvedTargetPrice:null,approvedScenarios:null,proposedValuationAction:'no-automatic-change',evidenceCitations:[],analystQuestions:[],interpretations:[],suggestedScenarioReview:[]});
it('shows at most three home tasks, opens the full inbox and routes to the correct AI draft',async()=>{
 const fetch=vi.fn(async(url:string,_options?:RequestInit)=>({ok:true,json:async()=>url.includes('report-intake')?{...intake,documents:[]}:{version:1,drafts:[1,2,3,4].map(draft)}}));vi.stubGlobal('fetch',fetch);
 const open=vi.fn();render(<ResearchTaskCenter news={[]} onOpen={open}/>);
 await waitFor(()=>expect(screen.getAllByRole('button',{name:'פתיחת הטיוטה'})).toHaveLength(3));
 fireEvent.click(screen.getAllByRole('button',{name:'פתיחת הטיוטה'})[0]);expect(open).toHaveBeenCalledWith(expect.any(String),'ai');
 fireEvent.click(screen.getByRole('button',{name:'לכל משימות המחקר'}));const modal=screen.getByRole('dialog',{name:'משימות המחקר'});
 expect(within(modal).getAllByRole('button',{name:'פתיחת הטיוטה'})).toHaveLength(4);
 fireEvent.click(within(modal).getAllByRole('button',{name:'סימון כטופל'})[0]);expect(within(modal).getAllByRole('button',{name:'פתיחת הטיוטה'})).toHaveLength(3);
 expect(Object.keys(JSON.parse(localStorage.getItem('pulse.research-tasks.v1')!))).toHaveLength(1);
 expect(fetch.mock.calls.every(([url,options])=>url.includes('/data/')&&!options?.body&&(!options?.method||options.method==='GET'))).toBe(true);
});
it('prioritizes pending model review and removes duplicates without modifying input',()=>{
 const ai={id:'ai',kind:'ai',companyId:'a',ticker:'A',title:'Draft',reason:'Review',date:'2026-10-30',destination:'ai'} as ResearchTask;
 const model={...ai,id:'model',kind:'model',date:'2026-10-20',destination:'valuation'} as ResearchTask;
 const original=[ai,model,ai];expect(prioritizeTasks(original,{}).map(t=>t.id)).toEqual(['model','ai']);
 expect(prioritizeTasks(original,{model:'done'}).map(t=>t.id)).toEqual(['ai']);expect(original).toHaveLength(3);
});
