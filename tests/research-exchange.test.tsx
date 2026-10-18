// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {parseAnalysis,applyAnalysis,analysisContract} from '../src/research/exchange';
import {ResearchExchange} from '../src/components/ResearchExchange';
import {blankResearch,initialState} from '../src/data/initial';
import {validState} from '../src/state/storage';
import {officialRegistry,officialCompany,parseOfficialSnapshot} from '../src/data/official';
import {officialPack} from '../src/research/officialPack';
import official from '../public/data/official-sources.json';
import type {ResearchField} from '../src/types';
const company={id:'candidate-nebius',name:'Nebius Group',label:'NBIS'};
function payload(id=company.id){return {version:1,companyId:id,asOf:'2026-10-18',fields:{...Object.fromEntries(Object.entries(blankResearch()).filter(([k])=>k!=='notes')),thesis:'NEW THESIS',risks:'NEW RISK'},sourceUrls:['https://nebius.com/financials'],missing:['Test missing data']};}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('covers every tracked company, including four distinct Israeli identities',()=>{
 expect(officialRegistry.companies).toHaveLength(11);
 const snap=parseOfficialSnapshot(official);
 for(const c of officialRegistry.companies){
  const found=officialCompany(c.ticker,c.name);expect(found?.id).toBe(c.id);
  expect(officialPack(c.id,snap)).toContain(`"companyId": "${c.id}"`);
  expect(parseAnalysis(JSON.stringify(payload(c.id)),c.id).companyId).toBe(c.id);
 }
 expect(officialCompany('', 'גילת טלקום')?.id).toBe('candidate-gilat-telecom');
 expect(officialCompany('GILT','Gilat Satellite Networks')).toBeUndefined();
});
it('rejects wrong company, malformed fields, bad dates, oversized data and unsafe URLs',()=>{
 for(const change of [
  (p:any)=>p.companyId='candidate-iren', (p:any)=>p.asOf='2026-02-30',
  (p:any)=>p.fields.thesis={text:'bad'}, (p:any)=>p.fields.extra='unknown',
  (p:any)=>p.sourceUrls=['javascript:alert(1)'],(p:any)=>p.sourceUrls=['https://user:pass@example.org'],
  (p:any)=>p.fields.thesis='x'.repeat(5001),
 ]){const p=payload();change(p);expect(()=>parseAnalysis(JSON.stringify(p),company.id)).toThrow();}
 expect(()=>parseAnalysis('x'.repeat(150001),company.id)).toThrow();
});
it('does not erase empty fields or notes and preserves a restorable prior version',()=>{
 const current={...blankResearch(),thesis:'OLD THESIS',revenue:'KEEP REVENUE',notes:[{id:'note',createdAt:'2026-10-17T12:00:00Z',text:'KEEP NOTE'}]};
 const p=parseAnalysis(JSON.stringify(payload()),company.id);
 const next=applyAnalysis(current,p,['thesis']);expect(next.thesis).toBe('NEW THESIS');expect(next.risks).toBe('');expect(next.revenue).toBe('KEEP REVENUE');
 expect(next.notes).toEqual(current.notes);expect(current.thesis).toBe('OLD THESIS');expect(next.versions?.[0].fields.thesis).toBe('OLD THESIS');
 expect(next.importInfo?.appliedFields).toEqual(['thesis']);
 const state={...initialState(),research:{NBIS:next}};expect(validState(JSON.parse(JSON.stringify(state)))).toBe(true);
 let r=next;for(let i=0;i<5;i++)r=applyAnalysis(r,p,['thesis']);expect(r.versions).toHaveLength(3);
 expect(()=>applyAnalysis(current,p,['revenue'])).toThrow();
});
it('previews changes without applying until the explicit apply button',()=>{
 const changed=vi.fn();render(<ResearchExchange company={company} current={{...blankResearch(),thesis:'OLD THESIS'}} onChange={changed} onPrepare={()=>{}}/>);
 fireEvent.change(screen.getByRole('textbox',{name:'ניתוח להחזרה',hidden:true}),{target:{value:JSON.stringify(payload())}});
 fireEvent.click(screen.getByText('בדיקה ותצוגה מקדימה'));expect(changed).not.toHaveBeenCalled();
 expect(screen.getByText('OLD THESIS')).toBeTruthy();expect(screen.getByText('NEW THESIS')).toBeTruthy();
 fireEvent.click(screen.getByText('החלת השדות שבחרתי בטיוטה'));expect(changed).toHaveBeenCalledTimes(1);
});
it('prepares a local-text pack with identity and source limitations',()=>{
 const prepare=vi.fn();render(<ResearchExchange company={company} current={blankResearch()} onChange={()=>{}} onPrepare={prepare}/>);
 fireEvent.change(screen.getByLabelText('טקסט המסמך'),{target:{value:'USER PROVIDED DOCUMENT TEXT'}});
 fireEvent.click(screen.getByText('הכנת ניתוח מהמסמך ל־NBIS'));
 const text=prepare.mock.calls[0][0];expect(text).toContain('USER PROVIDED DOCUMENT TEXT');expect(text).toContain('לא הוזן — אין להמציא מקור');expect(text).toContain(analysisContract(company.id));
});
