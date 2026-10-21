// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {ThesisMonitor} from '../src/components/ThesisMonitor';
import {thesisMonitors} from '../src/research/thesisMonitoring';

vi.mock('../src/hooks/useReportIntake',()=>({
 useReportIntake:()=>({data:{version:1,generatedAt:'2026-10-21T00:00:00Z',parserVersion:'test',documents:[],sources:[],notice:'test'},failed:false}),
}));

afterEach(cleanup);
it('shows a read-only report coverage summary without inventing comparable results',()=>{
 const monitor=thesisMonitors[0];
 render(<ThesisMonitor companyId={monitor.companyId}/>);
 expect(screen.getByLabelText('סיכום השוואת דוחות').textContent).toContain('מדדים בני השוואה: 0/6');
 expect(screen.getByLabelText('סיכום השוואת דוחות').textContent).toContain('דורשים בדיקה: 0');
 expect(screen.getByLabelText('סיכום השוואת דוחות').textContent).toContain('ממתינים לנתונים מתאימים: 6');
});
