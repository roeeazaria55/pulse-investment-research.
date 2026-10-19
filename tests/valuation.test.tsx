// @vitest-environment jsdom
import {it,expect,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {valueScenario} from '../src/research/valuation';
import {NbisValuation} from '../src/components/NbisValuation';
afterEach(cleanup);
const x={revenue:6000,multiple:5,cash:3000,debt:15000,shares:325,discount:12,years:1.2};
it('bridges enterprise to diluted equity and discounts by the horizon',()=>{
 const r=valueScenario(x)!;expect(r.enterprise).toBe(30000);expect(r.equity).toBe(18000);expect(r.terminal).toBeCloseTo(18000/325);expect(r.present).toBeCloseTo((18000/325)/1.12**1.2);
 expect(valueScenario({...x,debt:40000})!.terminal).toBe(0);
 expect(valueScenario({...x,shares:650})!.present).toBeCloseTo(r.present/2);
});
it('rejects zero shares, nonfinite and negative inputs',()=>{
 for(const invalid of [{shares:0},{debt:NaN},{revenue:Infinity},{cash:-1}])expect(valueScenario({...x,...invalid})).toBeNull();
});
it('restores the original model and never silently normalizes altered probabilities',()=>{
 render(<NbisValuation/>);fireEvent.click(screen.getByText('NBIS · המודל שלנו ל־12 חודשים'));
 expect(screen.getAllByText('$248.50')).toHaveLength(2);
 fireEvent.change(screen.getByLabelText('הסתברות דוב (%)'),{target:{value:'30'}});
 expect(screen.getByRole('alert')).toBeTruthy();
 fireEvent.click(screen.getByText('שחזור המודל המקורי'));
 expect(screen.queryByRole('alert')).toBeNull();
 expect(screen.getAllByText('$248.50')).toHaveLength(2);
 expect(screen.getAllByText(/שינויי המחשבון זמניים/).length).toBeGreaterThan(0);
 expect(screen.queryByText(/92.04/)).toBeNull();
});
