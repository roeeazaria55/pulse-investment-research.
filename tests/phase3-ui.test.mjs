// @vitest-environment jsdom
import React from 'react';
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup,within} from '@testing-library/react';
import App from '../src/App';
import fixture from './fixtures/demo-feed.json';
import {WhyImportant,NotificationsPanel} from '../src/components/PhaseThree';
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();history.replaceState(null,'','/');});
it('explains evidence dimensions rather than price prediction',()=>{
  render(React.createElement(WhyImportant,{rating:{eventLabel:'מימון או גיוס',eventScore:55,why:'TEST: headline only cannot prove materiality',sourceReliability:'ייחוס בלבד',companyRelevance:'direct',confidence:'medium',basis:'headline-only',version:'evidence-3.1'}}));
  fireEvent.click(screen.getByText(/למה זה חשוב/));
  expect(screen.getByText('כותרת בלבד')).toBeTruthy();expect(screen.getByText(/אינה תחזית מחיר/)).toBeTruthy();expect(screen.getByText(/אישורים עצמאיים/)).toBeTruthy();
});
it('keeps read state local and filters it without altering portfolio storage',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>fixture}));vi.stubGlobal('scrollTo',vi.fn());
  render(React.createElement(App));await screen.findByText('מצב הדגמה');
  fireEvent.click(within(screen.getByRole('navigation',{name:'ניווט נייד'})).getByRole('button',{name:'חדשות',exact:true}));
  const first=screen.getAllByRole('article')[0];fireEvent.click(within(first).getByRole('button',{name:'סימון כנקרא'}));
  fireEvent.change(screen.getByRole('combobox',{name:'מצב קריאה'}),{target:{value:'read'}});
  expect(screen.getAllByRole('article')).toHaveLength(1);expect(JSON.parse(localStorage.getItem('pulse-read-news-v1'))).toHaveLength(1);
});
it('exposes an honest test workflow and never asks for channel credentials in the app',()=>{
  render(React.createElement(NotificationsPanel,{open:true}));
  expect(screen.getByRole('link',{name:/שליחת התראת ניסיון דרך Actions/}).getAttribute('href')).toContain('notify-test.yml');
  expect(screen.queryByRole('textbox')).toBeNull();expect(screen.getByText(/אין עדיין הוכחה לקבלה בטלפון/)).toBeTruthy();
});
