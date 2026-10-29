import {describe,it,expect} from 'vitest';
import {summarizeCosts} from '../src/components/AISettingsPanel';

describe('AI budget status in owner settings',()=>{
 const now=new Date('2026-10-29T11:00:00Z');
 const hold={id:'a'.repeat(64),maxUsd:'0.75',heldAt:'2026-10-29T10:00:00Z'};
 const receipt={id:'b'.repeat(64),model:'gpt-6.1-sol',usd:'0.12',calledAt:'2026-10-29T10:00:00Z'};
 it('separates billed from reserved costs and never treats missing ledger as zero',()=>{
  const d=summarizeCosts({version:1,calls:[receipt],holds:[hold]},now);
  expect(d.spent).toBeCloseTo(.12);
  expect(d.reserved).toBeCloseTo(.75);
  expect(d.remaining).toBeCloseTo(8.13);
  expect(()=>summarizeCosts(null,now)).toThrow();
 });
 it('refuses forged or duplicate identifiers',()=>{
  expect(()=>summarizeCosts({version:1,calls:[receipt],holds:[{...hold,id:receipt.id}]},now)).toThrow();
  expect(()=>summarizeCosts({version:1,calls:[{...receipt,usd:'NaN'}],holds:[]},now)).toThrow();
  expect(()=>summarizeCosts({version:2,calls:[],holds:[]},now)).toThrow();
 });
 it('counts only the displayed UTC billing month',()=>{
  const prior={...receipt,calledAt:'2026-09-30T23:00:00Z'};
  expect(summarizeCosts({version:1,calls:[prior],holds:[]},now).spent).toBe(0);
 });
});
