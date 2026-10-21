import {expect,it,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {ThesisMonitor} from '../src/components/ThesisMonitor';
import {thesisMonitors} from '../src/research/thesisMonitoring';

vi.mock('../src/hooks/useReportIntake',()=>({
 useReportIntake:()=>({data:{version:1,generatedAt:'2026-10-21T00:00:00Z',parserVersion:'test',documents:[],sources:[],notice:'test'},failed:false}),
}));

it('shows a read-only report coverage summary without inventing comparable results',()=>{
 const monitor=thesisMonitors[0];
 render(<ThesisMonitor companyId={monitor.companyId}/>);
 expect(screen.getByLabelText('סיכום השוואת דוחות')).toHaveTextContent('מדדים בני השוואה: 0/6');
 expect(screen.getByLabelText('סיכום השוואת דוחות')).toHaveTextContent('דורשים בדיקה: 0');
 expect(screen.getByLabelText('סיכום השוואת דוחות')).toHaveTextContent('ממתינים לנתונים מתאימים: 6');
});
