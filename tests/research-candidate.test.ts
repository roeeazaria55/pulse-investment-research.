import {expect,it} from 'vitest';
import {previewResearchCandidate,validateResearchCandidate} from '../src/research/researchCandidate';
const candidate=()=>({version:1,companyId:'candidate-gilat-telecom',source:{filename:'PULSE_Gilat_Telecom_Full_Research_HE.pdf',sha256:'a'.repeat(64),asOf:'2026-10-21',verification:'unverified',sourceUrls:[] as string[]},valuation:{currency:'ILA',shareUnit:'share',reference:{value:205.6,asOf:'2026-10-20'},horizon:{date:'2027-12-31',earningsPeriod:'2027',note:'end 2027'},declaredWeighted:249.8,scenarios:[{id:'bear',probability:25,statedPrice:125,rationale:'dilution risk'},{id:'base',probability:55,statedPrice:245,rationale:'margin improvement'},{id:'bull',probability:20,statedPrice:419,rationale:'strong cash conversion'}]}});
it('accepts a candidate with agorot not silently converting to shekels',()=>{const x=validateResearchCandidate(candidate(),'candidate-gilat-telecom');expect(x.valuation.currency).toBe('ILA');});
it('returns a source/valuation preview without modifying the original or active state',()=>{
 const a=validateResearchCandidate(candidate(),'candidate-gilat-telecom');const b=structuredClone(a);b.valuation.scenarios[1].statedPrice=255;
 const diffs=previewResearchCandidate(a,b);expect(diffs.map(d=>d.path)).toEqual(['valuation.scenarios.base']);expect(a.valuation.scenarios[1].statedPrice).toBe(245);
});
it('rejects bad company, hashes, dates, missing evidence and wrong probability total',()=>{
 const a=candidate();expect(()=>validateResearchCandidate(a,'candidate-iren')).toThrow();
 a.valuation.scenarios[0].probability=20;expect(()=>validateResearchCandidate(a,a.companyId)).toThrow();
 a.valuation.scenarios[0].probability=25;a.source.sha256='invalid';expect(()=>validateResearchCandidate(a,a.companyId)).toThrow();
 a.source.sha256='a'.repeat(64);a.source.sourceUrls=['http://example.com'];expect(()=>validateResearchCandidate(a,a.companyId)).toThrow();
});
