// @vitest-environment jsdom
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {ReadingMode} from '../src/components/ReadingMode';
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();});
it('keeps one article, restores a saved chapter and font without changing financial data',()=>{
 HTMLElement.prototype.scrollIntoView=vi.fn();vi.stubGlobal('requestAnimationFrame',(f:()=>void)=>{f();return 1;});
 localStorage.setItem('pulse.reader.position.v1:report-v1','chapter-2');localStorage.setItem('pulse.reader.font.v1','20');
 render(<ReadingMode id="report-v1" title="קריאה נקייה" chapters={[{id:'chapter-1',label:'פתיחה'},{id:'chapter-2',label:'תזרים'}]}><h4 id="chapter-1" data-reading-anchor tabIndex={-1}>פרק ראשון</h4><h4 id="chapter-2" data-reading-anchor tabIndex={-1}>פרק שני</h4><p>מחיר יעד שמור: 100</p></ReadingMode>);
 expect((screen.getByLabelText('גודל טקסט בקריאה') as HTMLSelectElement).value).toBe('20');
 fireEvent.click(screen.getByRole('button',{name:'המשך מהמקום ששמרתי'}));expect(document.activeElement?.id).toBe('chapter-2');
 fireEvent.click(screen.getByRole('button',{name:'מצב קריאה נקי'}));expect(screen.getByRole('dialog',{name:'קריאה נקייה'})).toBeTruthy();
 expect(screen.getAllByText('מחיר יעד שמור: 100')).toHaveLength(1);
 fireEvent.change(screen.getByLabelText('גודל טקסט בקריאה'),{target:{value:'22'}});expect(localStorage.getItem('pulse.reader.font.v1')).toBe('22');
 fireEvent.click(screen.getByRole('button',{name:'סגירה'}));expect(screen.queryByRole('dialog')).toBeNull();
 expect(screen.getByText('מחיר יעד שמור: 100')).toBeTruthy();
});
