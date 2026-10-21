// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import raw from '../public/data/report-intake.json';
import {ReportIntake} from '../src/components/ReportIntake';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('shows IREN coverage gaps when the snapshot contains no intake entry for it',async()=>{
 const data=structuredClone(raw);data.documents=data.documents.filter(d=>d.companyId!=='candidate-iren');data.sources=data.sources.filter(s=>s.companyId!=='candidate-iren');
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
 render(<ReportIntake companyId="candidate-iren"/>);
 fireEvent.click(screen.getByText('קליטת דוחות אוטומטית'));
 await waitFor(()=>expect(screen.getByText('אין רישום קליטת דוחות לחברה בתמונת הנתונים הנוכחית.')).toBeTruthy());
 const gaps=within(screen.getByLabelText('פערי כיסוי פיננסי של IREN'));
 expect(gaps.getByText(/0 מסמכי מקור/)).toBeTruthy();
 expect(gaps.getByText(/שנת כספים המסתיימת ביוני/)).toBeTruthy();
 expect(gaps.queryByText(/snapshot/)).toBeNull();
});

it('shows table-only NBIS gaps alongside links to the issuer documents that were read',async()=>{
 const data=structuredClone(raw);for(const d of data.documents.filter(d=>d.companyId==='candidate-nebius'))d.facts=[];
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
 render(<ReportIntake companyId="candidate-nebius"/>);
 await waitFor(()=>expect(screen.getByText(/מסמכים נקראו/)).toBeTruthy());
 fireEvent.click(screen.getByText(/קליטת דוחות אוטומטית/));
 const gaps=within(screen.getByLabelText('פערי כיסוי פיננסי של NBIS'));
 expect(gaps.getByText(/טבלאות וטקסט דורשים מתאם מקור/)).toBeTruthy();
 expect(gaps.getByText(/קבוצה מאוחדת בנפרד מ־AI Cloud/)).toBeTruthy();
 const doc=data.documents.find(d=>d.companyId==='candidate-nebius')!;
 fireEvent.click(screen.getByText(doc.title));
 expect(screen.getAllByRole('link',{name:'פתיחת הדיווח הרשמי ↗'}).some(a=>a.getAttribute('href')===doc.finalUrl)).toBe(true);
});

it('does not label an unavailable snapshot as proof of missing issuer reports',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(Error('offline')));
 render(<ReportIntake companyId="candidate-iren"/>);
 fireEvent.click(screen.getByText('קליטת דוחות אוטומטית'));
 await waitFor(()=>expect(screen.getByText('מצב הקליטה אינו זמין. אין להסיק מכך שלא פורסם דוח.')).toBeTruthy());
 expect(screen.getByText('מצב קליטת הדוחות אינו זמין; לא ניתן לקבוע כיסוי נתונים.')).toBeTruthy();
 expect(screen.queryByText('טרם נקלט תוכן דוח רשמי לחברה במאגר הזה.')).toBeNull();
});

it.each(['failed','no-candidates'] as const)('distinguishes IREN %s from a missing intake entry or an unpublished report',async status=>{
 const data=structuredClone(raw);data.documents=data.documents.filter(d=>d.companyId!=='candidate-iren');data.sources=data.sources.filter(s=>s.companyId!=='candidate-iren');
 data.sources.push({companyId:'candidate-iren',lastAttemptAt:data.generatedAt,status,error:status==='failed'?'HTTP 403: Forbidden':null});
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>data}));
 render(<ReportIntake companyId="candidate-iren"/>);
 fireEvent.click(screen.getByText('קליטת דוחות אוטומטית'));
 if(status==='failed')await waitFor(()=>expect(screen.getByText('HTTP 403: Forbidden')).toBeTruthy());
 else await waitFor(()=>expect(screen.getByText(/לא נמצאה רשומת דוח מתאימה במאגר הנוכחי; אין בכך קביעה שלא פורסם דוח/)).toBeTruthy());
 expect(screen.queryByText('אין רישום קליטת דוחות לחברה בתמונת הנתונים הנוכחית.')).toBeNull();
});
