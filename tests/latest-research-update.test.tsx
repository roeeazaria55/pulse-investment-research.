// @vitest-environment jsdom
import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, render, screen, fireEvent} from '@testing-library/react';
import registry from '../public/data/official-registry.json';
import {LatestResearchUpdate, parseLatestSnapshot, parseResearchHistory, verifiedLink, type LatestReport} from '../src/components/LatestResearchUpdate';

const missing=(companyId:string,ticker:string):LatestReport=>({
 companyId,ticker,status:'insufficient-evidence',kind:'no-verified-new-report',
 reportPeriod:null,publishedDate:null,sourceUrl:null,sourceVersion:null,
 metrics:[],modelReview:[],findings:[],questions:['אין נתון מאושר'],missing:['נתוני מקור חסרים'],
 aiAnalysisEnabled:false,reviewRequired:true,modelChange:'אין שינוי במחיר יעד.',contentId:null
});
function snapshot(){
 const dlo=missing('us-dlo-nasdaq-a','DLO');
 dlo.status='needs-reconciliation';
 dlo.reportPeriod='2026-Q2';
 dlo.publishedDate='2026-08-13';
 dlo.sourceVersion='a'.repeat(64);
 dlo.sourceDigestKind='retained-issuer-html-sha256';
 dlo.sourceUrl='https://rss.globenewswire.com/news-release/test';
 dlo.metrics=[{
  id:'revenue',label:'הכנסות',value:399.7,previousValue:null,changePercent:null,unit:'USD million',
  periodStart:'2026-04-01',periodEnd:'2026-06-30',accountingBasis:'IFRS',sourceRow:'Revenue',sourceRaw:'399.7',
  sourceUrl:dlo.sourceUrl,reviewStatus:'needs-reconciliation',comparison:'אין בסיס קודם מאושר'
 }];
 dlo.activeValuationContext={status:'unverified-supplied-research',scenario:'base',baseTargetPerShare:21.14,weight:50,currency:'USD',asOf:'2026-10-20',source:'src/data/suppliedResearch.json',pdfFilename:'PULSE_DLO_Full_Research_HE.pdf',isComparableFinancialActual:false,note:'מחקר שסופק'};
 dlo.modelReview=[{metricId:'revenue',status:'not-comparable-period-or-definition',modelScenario:null,
  modelStatus:'archived-secondary',modelInput:null,modelValue:null,modelUnit:null,modelPeriod:null,modelLabel:'הכנסות Q2 במחקר קודם',
  modelAsOf:'2026-10-19',modelSource:'src/data/models/dlo.json',researchAsOf:'2026-10-20',
  researchSource:'src/data/research/dlo.json',researchTextMatch:true,reason:'תקופה שונה',
  analystReview:'אין שינוי שווי',automaticChange:false}];
 return {version:1,generatedAt:'2026-10-25T10:00:00Z',aiStatus:'not-enabled',notice:'Review only',
  reports:[dlo,missing('candidate-iren','IREN'),missing('candidate-nebius','NBIS'),missing('us-smci-nasdaq-common','SMCI'),
   ...registry.companies.filter(c=>!['us-dlo-nasdaq-a','candidate-iren','candidate-nebius','us-smci-nasdaq-common'].includes(c.id))
    .map(c=>missing(c.id,c.label))]};
}
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
it('displays retained real-value-shaped DLO research with honest review status and manual action',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>snapshot()}));
 const prepare=vi.fn();
 render(<LatestResearchUpdate companyId="us-dlo-nasdaq-a" onPrepare={prepare}/>);
 expect(await screen.findByText(/399.7 USD million/)).toBeTruthy();
 expect(screen.getByText(/מקור DLO דורש בירור/)).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:/הכנת שאלות למחקר/}));
 expect(prepare).toHaveBeenCalledOnce();
 expect(prepare.mock.calls[0][0]).toContain('399.7');
 expect(prepare.mock.calls[0][0]).toContain('אל תשנה אוטומטית');
});
it('shows missing evidence for SMCI without invented values',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>snapshot()}));
 render(<LatestResearchUpdate companyId="us-smci-nasdaq-common"/>);
 expect(await screen.findByText(/אין עדכון פיננסי מבוסס מקור/)).toBeTruthy();
 expect(screen.queryByText(/399.7 USD million/)).toBeNull();
});
it('rejects hostile source and invalid amounts before rendering',()=>{
 const bad=snapshot();
 bad.reports[0].metrics[0].sourceUrl='https://evil.invalid/data';
 expect(()=>parseLatestSnapshot(bad)).toThrow();
 expect(verifiedLink('javascript:alert(1)','candidate-iren')).toBeNull();
});

it('shows an explicitly monitored company without invented financial data',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>snapshot()}));
 render(<LatestResearchUpdate companyId="candidate-enlight"/>);
 expect(await screen.findByText(/אין עדכון פיננסי מבוסס מקור/)).toBeTruthy();
});
it('rejects inconsistent issuer digest and unauthorized automatic update',()=>{
 const bad=snapshot();
 bad.reports[0].modelReview![0].automaticChange=true as false;
 expect(()=>parseLatestSnapshot(bad)).toThrow();
 const other=snapshot();
 other.reports[0].sourceDigestKind='curated-extract-json-sha256-not-original-pdf';
 expect(()=>parseLatestSnapshot(other)).toThrow();
});

it('shows source-bound public research history without promoting it to new forecasts',async()=>{
 const data=snapshot();
 const original=data.reports[0];
 original.contentId='f'.repeat(24);
 const entry={companyId:original.companyId,ticker:'DLO',contentId:original.contentId,
  firstSeenAt:'2026-10-25T10:00:00Z',reportPeriod:original.reportPeriod,publishedDate:original.publishedDate,
  sourceVersion:original.sourceVersion,status:original.status,report:original};
 vi.stubGlobal('fetch',vi.fn().mockImplementation(async(url:string)=>({ok:true,json:async()=>url.includes('research-update-history')?
  {version:1,updatedAt:'2026-10-25T10:00:00Z',entries:[entry]}:data})));
 render(<LatestResearchUpdate companyId="us-dlo-nasdaq-a"/>);
 expect(await screen.findByText(/היסטוריית גרסאות מחקר \(1\)/)).toBeTruthy();
 expect(screen.getByText(/מועד יצירת קובץ הנתונים אינו מועד פרסום/)).toBeTruthy();
});
it('rejects duplicated or identity-swapped historical evidence',()=>{
 const data=snapshot();
 const original=data.reports[0];
 original.contentId='f'.repeat(24);
 const entry={companyId:original.companyId,ticker:'DLO',contentId:original.contentId,
  firstSeenAt:'2026-10-25T10:00:00Z',reportPeriod:original.reportPeriod,publishedDate:original.publishedDate,
  sourceVersion:original.sourceVersion,status:original.status,report:original};
 const h={version:1,updatedAt:'2026-10-25T10:00:00Z',entries:[entry]};
 expect(parseResearchHistory(h).entries).toHaveLength(1);
 expect(()=>parseResearchHistory({...h,entries:[entry,entry]})).toThrow();
 expect(()=>parseResearchHistory({...h,entries:[{...entry,companyId:'candidate-iren'}]})).toThrow();
});


it('covers every official company with a unique report row',()=>{
 const data=snapshot();
 expect(parseLatestSnapshot(data).reports).toHaveLength(registry.companies.length);
 const incomplete=snapshot();incomplete.reports.pop();
 expect(()=>parseLatestSnapshot(incomplete)).toThrow('מבנה');
 const duplicated=snapshot();duplicated.reports[1].companyId=duplicated.reports[0].companyId;
 expect(()=>parseLatestSnapshot(duplicated)).toThrow();
});

it('accepts a strictly retained SEC/XBRL comparison as unapproved evidence',()=>{
 const data=snapshot();
 const report=data.reports.find(r=>r.companyId==='us-smci-nasdaq-common')!;
 report.status='pending-review';report.kind='structured-sec-xbrl-review-only';
 report.sourceUrl='https://www.sec.gov/Archives/edgar/data/1375365/000137536526000022/smci-20260630.htm';
 report.sourceVersion='a'.repeat(64);report.sourceDigestKind='retained-sec-inline-xbrl-sha256';
 report.metrics=[{id:'revenue',label:'הכנסות',value:39063.072,previousValue:21972.042,changePercent:77.79,
   unit:'USD million',periodStart:'2025-07-01',periodEnd:'2026-06-30',
   accountingBasis:'US GAAP Revenue from Contracts — structured XBRL (needs review)',
   sourceRow:'us-gaap:revenuefromcontractwithcustomerexcludingassessedtax',sourceRaw:'39063072000',
   sourcePreviousRaw:'21972042000',sourcePage:null,sourceDocumentUrl:null,
   sourceUrl:report.sourceUrl,reviewStatus:'pending-review',
   comparison:'Same tagged duration; not a forecast surprise.'}];
 report.reportEvidence={id:'report:'+'f'.repeat(32),sha256:'a'.repeat(64),title:'SMCI FY2026 official SEC 10-K',
   format:'html',url:report.sourceUrl,publishedDate:null,documentPeriod:null,
   firstDetectedAt:'2026-10-20T00:00:00Z',lastSuccessfulAt:'2026-10-20T00:00:00Z',
   reviewStatus:'pending-review',sourceIsCurrentlyReachable:false,
   note:'Retained document, not proof of latest issuer filing.'};
 expect(parseLatestSnapshot(data).reports.find(r=>r.companyId===report.companyId)?.metrics[0].value).toBe(39063.072);
 report.reportEvidence.sha256='b'.repeat(64);
 expect(()=>parseLatestSnapshot(data)).toThrow('XBRL');
});
