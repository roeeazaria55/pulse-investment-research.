import {suppliedFor} from '../src/data/suppliedResearch';
import {it,expect} from 'vitest';
import {companyModels,companyModelFor} from '../src/data/companyModels';
import {modelValue,scenarioValue,inputKeys,type CompanyModel} from '../src/research/scenarioModel';
import {publishedFor} from '../src/data/publishedResearch';
it('covers every company with a calculated weighted target and a fixed 12-month horizon',()=>{
 expect(companyModels).toHaveLength(11);
 for(const m of companyModels){
  expect(m.horizonDate).toBe('2027-10-19');const r=modelValue(m)!;
  expect(r.weighted).toBeCloseTo(r.results[0].target*.2+r.results[1].target*.5+r.results[2].target*.3,8);
  expect(r.results[0].target).toBeLessThanOrEqual(r.results[1].target);expect(r.results[1].target).toBeLessThanOrEqual(r.results[2].target);
  const published=publishedFor(m.companyId)!.analysis.fields.valuation;
  if(suppliedFor(m.companyId))expect(published).toContain('$');
  else expect(published).toContain('יעד משוקלל:');
  expect(publishedFor(m.companyId)!.analysis.missing.some(s=>s.includes('אין מחיר יעד'))).toBe(false);
 }
});
it('calculates earnings after financing, tax, minority and preferred, then converts currency only once',()=>{
 const m=companyModelFor('candidate-enlight')!;const x={...m.scenarios[1].inputs,driver:100,margin:40,corporate:2,depreciation:3,netFinance:-5,tax:20,minority:1,preferred:1,shares:10,multiple:20,fx:3};
 const r=scenarioValue(m,x)!;expect(r.earnings).toBe(22);expect(r.eps).toBe(2.2);expect(r.target).toBe(132);
 expect(scenarioValue(m,{...x,fx:1})!.target).toBe(44);
 expect(scenarioValue(m,{...x,netFinance:-100})!.target).toBe(0);
});
it('uses equity sales for the insurer, without treating insurance reserves as surplus cash',()=>{
 const m=companyModelFor('us-lmnd-nyse-common')!;const r=scenarioValue(m,{revenue:100,shares:10,multiple:3,fx:1})!;
 expect(r.target).toBe(30);expect(r.enterprise).toBeNull();expect(r.earnings).toBeNull();
});
it('raises funding with fees and reconciles debt, cash and economic conversion without double counting',()=>{
 const m=structuredClone(companyModelFor('candidate-iren')!) as CompanyModel;
 m.capital={cash:10,shares:10,seniorDebt:10,notes:[{id:'note',original:10,claim:10,rate:1000}],warrants:[{shares:5,strike:2}]};
 const x={...m.scenarios[1].inputs,revenue:100,ebitdaMargin:50,multiple:2,knownFunding:0,facilityDebt:0,releasedCash:0,operatingCash:0,netAdvances:0,capex:20,acquisition:0,repayment:0,minimumCash:5,debtShare:50,issuePrice:3,newAwards:0,fees:0,noncore:0,accretion:0,fx:1};
 const r=scenarioValue(m,x)!;
 expect(r.gap).toBe(15);expect(r.newDebt).toBe(7.5);expect(r.newEquity).toBe(7.5);expect(r.fundingShares).toBe(2.5);
 expect(r.converted).toEqual(['note']);expect(r.shares).toBe(27.5);expect(r.cash).toBe(15);expect(r.debt).toBe(17.5);
 expect(r.target).toBeCloseTo((100+15-17.5)/27.5,8);
 const fees=scenarioValue(m,{...x,fees:2})!;expect(fees.newDebt+fees.newEquity).toBeCloseTo(15/.98);
 expect(scenarioValue(m,{...x,capex:30})!.target).toBeLessThan(r.target);
});
it('retains principal on underwater notes and floors negative residual equity at zero',()=>{
 const m=companyModelFor('candidate-iren')!,r=scenarioValue(m,m.scenarios[0].inputs)!;
 expect(r.target).toBe(0);expect(r.converted).toHaveLength(0);
});
it('rejects missing, nonfinite and inconsistent inputs instead of recycling a prior target',()=>{
 for(const m of companyModels){
  const x=m.scenarios[1].inputs;
  for(const key of inputKeys(m.method))expect(scenarioValue(m,{...x,[key]:NaN})).toBeNull();
  expect(scenarioValue(m,{...x,fx:0})).toBeNull();
  expect(modelValue(m,m.scenarios.map((s,i)=>({...s,probability:i===0?30:s.probability})))).toBeNull();
 }
 const m=companyModelFor('candidate-nebius')!;
 expect(scenarioValue(m,{...m.scenarios[1].inputs,fees:100})).toBeNull();
 expect(scenarioValue(m,{...m.scenarios[1].inputs,debtShare:101})).toBeNull();
});
it('keeps NBIS original targets separate and does not fit the new model to them',()=>{
 expect(modelValue(companyModelFor('candidate-nebius')!)!.weighted).not.toBeCloseTo(248.5);
 expect(publishedFor('candidate-nebius')!.analysis.fields.valuation).toContain('182.3');
});
