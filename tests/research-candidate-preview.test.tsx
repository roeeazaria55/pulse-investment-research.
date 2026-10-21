// @vitest-environment jsdom
import {it,expect,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {ResearchCandidatePreview} from '../src/components/ResearchCandidatePreview';
afterEach(cleanup);
const payload=()=>({version:1,companyId:'candidate-gilat-telecom',source:{filename:'Gilat.pdf',sha256:'a'.repeat(64),asOf:'2026-10-21',verification:'unverified',sourceUrls:[]},valuation:{currency:'ILA',shareUnit:'share',reference:null,horizon:{date:'2027-12-31',earningsPeriod:'2027',note:'forecast'},declaredWeighted:249.8,scenarios:[{id:'bear',probability:25,statedPrice:125,rationale:'risk'},{id:'base',probability:55,statedPrice:245,rationale:'trend'},{id:'bull',probability:20,statedPrice:419,rationale:'growth'}]}});
it('previews a candidate without exposing an apply action',()=>{
 render(<ResearchCandidatePreview companyId="candidate-gilat-telecom"/>);
 const field=screen.getByRole('textbox',{name:'JSON מחקר מועמד'});
 fireEvent.change(field,{target:{value:JSON.stringify(payload())}});
 fireEvent.click(screen.getByRole('button',{name:'בדיקת מחקר מועמד'}));
 expect(screen.getByText(/שווי משוקלל מחושב:/).textContent).toContain('249.800');
 expect(screen.queryByRole('button',{name:/החל|אשר|שמור/})).toBeNull();
});
it('rejects a candidate intended for a different company',()=>{
 render(<ResearchCandidatePreview companyId="candidate-iren"/>);
 fireEvent.change(screen.getByRole('textbox',{name:'JSON מחקר מועמד'}),{target:{value:JSON.stringify(payload())}});
 fireEvent.click(screen.getByRole('button',{name:'בדיקת מחקר מועמד'}));
 expect(screen.getByRole('alert').textContent).toMatch(/מזהה חברה/);
});
