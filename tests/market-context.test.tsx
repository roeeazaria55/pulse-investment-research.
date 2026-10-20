// @vitest-environment jsdom
import {afterEach,it,expect} from 'vitest';
import {render,screen,fireEvent,cleanup,within} from '@testing-library/react';
import {MacroPanel,NextEarnings,WeeklyEarnings} from '../src/components/MarketContext';
import {earningsEvents,eventsInWeek,israelDay,nextEarnings,weekStart} from '../src/research/earningsCalendar';
import {researchTarget} from '../src/research/researchTarget';
import {OriginalSandisk} from '../src/components/OriginalSandisk';
import {publishedFor} from '../src/data/publishedResearch';
import type {Intelligence} from '../src/intelligenceTypes';
afterEach(cleanup);
it('uses Jerusalem dates, Sunday weeks and civil dates across the DST boundary',()=>{
 expect(israelDay(new Date('2026-10-24T22:30:00Z'))).toBe('2026-10-25');
 expect(weekStart('2026-10-31')).toBe('2026-10-25');
 expect(weekStart('2026-11-01')).toBe('2026-11-01');
 const events=earningsEvents();expect(events).toHaveLength(11);
 expect(eventsInWeek(events,'2026-10-25').map(e=>e.securityId)).toEqual(['candidate-ftai','candidate-sandisk']);
 expect(nextEarnings('us-meta-nasdaq-a',undefined,'2026-10-22')).toBeUndefined();
});
it('prefers collected revisions, labels estimates and never shows a past date as the next report',()=>{
 const e={...earningsEvents()[0],date:'2026-11-05',status:'estimated' as const,eventKind:'results-date' as const};
 const intel={calendar:{events:[e]}} as Intelligence;
 expect(nextEarnings(e.securityId,intel,'2026-10-20')!.date).toBe('2026-11-05');
 render(<NextEarnings companyId={e.securityId} intel={intel} today="2026-10-20"/>);
 expect(screen.getByText(/מועד משוער/)).toBeTruthy();cleanup();
 render(<NextEarnings companyId="us-meta-nasdaq-a" today="2026-10-22"/>);
 expect(screen.getByText(/טרם אומת מועד עתידי/)).toBeTruthy();
});
it('navigates weeks, distinguishes calls from results, and keeps unknown companies visible',()=>{
 render(<WeeklyEarnings today="2026-10-20"/>);
 expect(within(screen.getByText('כל המועדים העתידיים הידועים (6)').closest('details')!).getByText('SanDisk')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'השבוע הבא'}));
 const events=document.querySelector('.weekly-events')! as HTMLElement;
 expect(within(events).getByText('SanDisk')).toBeTruthy();expect(within(events).getByText(/שיחת משקיעים · Q1 FY2027/)).toBeTruthy();
 expect(document.querySelectorAll('[id^="earnings-"]')).toHaveLength(new Set([...document.querySelectorAll('[id^="earnings-"]')].map(e=>e.id)).size);
 expect(screen.getByText('ללא מועד עתידי מאומת (5)')).toBeTruthy();
});
it('marks analysis stale after a scheduled decision, without treating headline collection as analysis',()=>{
 render(<MacroPanel today="2026-10-22"/>);
 expect(screen.getByText(/חלף מועד של אירוע מאקרו/)).toBeTruthy();
 expect(screen.getByText(/אינם מעדכנים אוטומטית את הניתוח/)).toBeTruthy();
 expect(screen.getByText('3.7%')).toBeTruthy();expect(screen.getByText('1.6%')).toBeTruthy();
});
it('restores original targets consistently and does not invent missing Sandisk probabilities',()=>{
 expect(researchTarget('candidate-nebius')!.target).toBe(248.5);
 expect(researchTarget('candidate-sandisk')!.target).toBe(1900);expect(researchTarget('candidate-sandisk')!.approximate).toBe(true);
 expect(publishedFor('candidate-sandisk')!.analysis.fields.valuation).toContain('המשקולות והגישור הפיננסי לא שוחזרו');
 expect(publishedFor('candidate-nebius')!.analysis.fields.base).toContain('235');
 render(<OriginalSandisk/>);expect(screen.getAllByText('המשקל המקורי לא שוחזר')).toHaveLength(3);
 expect(screen.queryByRole('spinbutton')).toBeNull();
});
