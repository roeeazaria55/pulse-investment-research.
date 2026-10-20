// @vitest-environment jsdom
import {it,expect,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {CompanyValuation} from '../src/components/CompanyValuation';
afterEach(cleanup);
it('recalculates from assumptions, rejects invalid weights, resets and clears edits on close',()=>{
 render(<CompanyValuation companyId="us-meta-nasdaq-a"/>);
 const open=screen.getByText('תרחישים, חישוב ורגישויות · META');fireEvent.click(open);
 const original=screen.getByTestId('weighted-model-target').textContent;
 fireEvent.change(screen.getByLabelText('מכפיל במועד היעד · בסיס'),{target:{value:'10'}});
 expect(screen.getByTestId('weighted-model-target').textContent).not.toBe(original);
 fireEvent.change(screen.getByLabelText('משקל דוב במודל (%)'),{target:{value:'30'}});expect(screen.getByRole('alert')).toBeTruthy();
 fireEvent.click(screen.getByText('שחזור הנחות המודל המחושב'));expect(screen.queryByRole('alert')).toBeNull();
 expect(screen.getByTestId('weighted-model-target').textContent).toBe(original);
 fireEvent.change(screen.getByLabelText('מכפיל במועד היעד · בסיס'),{target:{value:''}});expect(screen.getByRole('alert')).toBeTruthy();
 fireEvent.click(open);fireEvent.click(open);expect(screen.getByTestId('weighted-model-target').textContent).toBe(original);
});
it('does not invent local quotes or upside and explicitly distinguishes ILS from agorot',()=>{
 render(<CompanyValuation companyId="candidate-gilat-telecom"/>);fireEvent.click(screen.getByText('תרחישים, חישוב ורגישויות · GLTL'));
 expect(screen.queryByText('אפסייד במחיר מול הייחוס המתוארך')).toBeNull();
 expect(screen.getAllByText('מחיר באגורות למניה')).toHaveLength(3);
 fireEvent.change(screen.getByLabelText('מחיר ייחוס ב־ILS'),{target:{value:'2'}});
 fireEvent.change(screen.getByLabelText('תאריך הייחוס למודל'),{target:{value:'2026-10-19'}});
 expect(screen.getByText('אפסייד במחיר מול הייחוס המתוארך')).toBeTruthy();
 fireEvent.change(screen.getByLabelText('תאריך הייחוס למודל'),{target:{value:'2026-02-30'}});
 expect(screen.queryByText('אפסייד במחיר מול הייחוס המתוארך')).toBeNull();
});
