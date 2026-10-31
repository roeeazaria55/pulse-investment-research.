// @vitest-environment jsdom
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {ModelReviewInbox} from '../src/components/ModelReviewInbox';
import intake from '../public/data/report-intake.json';
afterEach(()=>{cleanup();vi.unstubAllGlobals();localStorage.clear();vi.useRealTimers();});
it('offers a correctly identified company action and local read acknowledgement without financial writes',async()=>{
 const data=structuredClone(intake);
 const doc=data.documents.find(d=>d.companyId==='us-smci-nasdaq-common')!;
 doc.publishedDate='2026-10-29';doc.status='extracted';doc.url=doc.url+'?review-fixture=1';doc.finalUrl=doc.url;
 const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>data});vi.stubGlobal('fetch',fetch);
 const open=vi.fn();render(<ModelReviewInbox companyId={doc.companyId} onOpen={open}/>);
 await screen.findByText('1 לבדיקה');
 fireEvent.click(screen.getByRole('button',{name:'בדיקת המודל'}));expect(open).toHaveBeenCalledWith(doc.companyId);
 fireEvent.click(screen.getByRole('button',{name:'סימון כנקרא'}));
 expect(screen.queryByRole('button',{name:'בדיקת המודל'})).toBeNull();
 expect(JSON.parse(localStorage.getItem('pulse.model-review-read.v1')!)).toHaveLength(1);
 expect(fetch).toHaveBeenCalledTimes(1);
 expect(fetch.mock.calls[0][0]).toContain('data/report-intake.json');
 expect(fetch.mock.calls[0][1]).not.toHaveProperty('body');
});
