// @vitest-environment jsdom
import {render,screen,cleanup} from '@testing-library/react';
import {afterEach,expect,it} from 'vitest';
import {ResearchIntakeStatus} from '../src/components/ResearchIntakeStatus';
afterEach(cleanup);
it('shows imported Gilat Telecom original without claiming issuer verification',()=>{
 render(<ResearchIntakeStatus companyId="candidate-gilat-telecom"/>);
 expect(screen.getByText('המחקר החדש טרם נקלט במלואו באתר')).toBeTruthy();
 expect(screen.getByText(/SHA-256/)).toBeTruthy();
 expect(screen.getByText(/פרטי קובץ מקור שמור במאגר/)).toBeTruthy();
 expect(screen.getByText(/תוכן פיננסי ממתין לאימות/)).toBeTruthy();
});
it('shows full published NBIS separately from source re-audit status',()=>{
 render(<ResearchIntakeStatus companyId="candidate-nebius"/>);
 expect(screen.getByText('מחקר מלא זמין לקריאה באתר')).toBeTruthy();
 expect(screen.getByText(/בדיקה חוזרת/)).toBeTruthy();
});
it('does not display a false research status for unknown company ids',()=>{
 const {container}=render(<ResearchIntakeStatus companyId="unknown-company"/>);
 expect(container.querySelector('[data-testid="research-intake-status"]')).toBeNull();
});
