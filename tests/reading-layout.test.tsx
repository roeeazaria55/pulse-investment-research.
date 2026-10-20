// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,within,cleanup,waitFor} from '@testing-library/react';
import App from '../src/App';
import fixture from './fixtures/demo-feed.json';
import {readableHeadline} from '../src/research/newsPresentation';
import {labels} from '../src/research/prompt';
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();history.replaceState(null,'','/');});
function setup(data=fixture){localStorage.clear();vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));vi.stubGlobal('scrollTo',vi.fn());render(<App/>);}
function nav(name:string){fireEvent.click(within(screen.getByRole('navigation',{name:'ניווט נייד'})).getByRole('button',{name,exact:true}));}
it('opens research with the selected company and overview, then switches tasks without losing a personal draft',async()=>{
 setup();await screen.findByText('מצב הדגמה');nav('מחקר');
 expect(screen.getByRole('combobox',{name:'חברה למחקר'})).toBeTruthy();
 expect(screen.getByRole('tab',{name:'סקירה'}).getAttribute('aria-selected')).toBe('true');
 expect(screen.queryByRole('region',{name:'מקורות רשמיים וחבילת מחקר'})).toBeNull();
 expect(screen.queryByRole('textbox',{name:labels.thesis})).toBeNull();
 fireEvent.click(screen.getByRole('tab',{name:'המחקר שלי'}));
 fireEvent.change(screen.getByRole('textbox',{name:labels.thesis}),{target:{value:'A draft stays with its company'}});
 fireEvent.click(screen.getByRole('tab',{name:'מודל שווי'}));
 expect(screen.getByRole('heading',{name:'NBIS · מודל מחושב ל־12 חודשים'})).toBeTruthy();
 fireEvent.click(screen.getByRole('tab',{name:'המחקר שלי'}));
 expect((screen.getByRole('textbox',{name:labels.thesis}) as HTMLTextAreaElement).value).toBe('A draft stays with its company');
 fireEvent.click(screen.getByRole('button',{name:'שמירת מחקר'}));
 expect(JSON.parse(localStorage.getItem('pulse.personal.v1')!).research.NBIS.thesis).toBe('A draft stays with its company');
});
it('pages a long news feed and resets pagination for a new search',async()=>{
 const data=structuredClone(fixture);data.news=Array.from({length:25},(_,i)=>({...fixture.news[0],id:`demo-page-${i}`,headline:`הדגמה: ידיעה מספר ${i}`,publishedAt:`2026-01-${String(i%9+1).padStart(2,'0')}T06:00:00Z`}));
 setup(data);await screen.findByText('מצב הדגמה');nav('חדשות');
 expect(screen.getAllByRole('article')).toHaveLength(12);
 expect((screen.getByRole('combobox',{name:'מצב קריאה'}).closest('details') as HTMLDetailsElement).open).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:/הצגת ידיעות נוספות/}));expect(screen.getAllByRole('article')).toHaveLength(24);
 fireEvent.change(screen.getByRole('textbox',{name:'חיפוש חדשות'}),{target:{value:'מספר 24'}});
 await waitFor(()=>expect(screen.getAllByRole('article')).toHaveLength(1));
 fireEvent.change(screen.getByRole('textbox',{name:'חיפוש חדשות'}),{target:{value:''}});
 await waitFor(()=>expect(screen.getAllByRole('article')).toHaveLength(12));
});
it('removes only a repeated exact publisher suffix, preserving the underlying headline',()=>{
 expect(readableHeadline('Company raises capital - Reuters','Reuters')).toBe('Company raises capital');
 expect(readableHeadline('Company raises capital - Another Company','Reuters')).toBe('Company raises capital - Another Company');
 expect(readableHeadline('Reuters','Reuters')).toBe('Reuters');
});
