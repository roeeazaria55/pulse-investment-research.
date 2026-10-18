// @vitest-environment jsdom
import {it,expect,vi,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {OfficialSources} from '../src/components/OfficialSources';
import {parseOfficialSnapshot,type OfficialSnapshot} from '../src/data/official';
import {officialPack} from '../src/research/officialPack';
import initial from '../public/data/official-sources.json';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
function fixture(){
 const f=structuredClone(initial) as OfficialSnapshot;const stamp='2026-10-18T16:00:00Z';
 f.generatedAt=stamp;
 f.sources=f.sources.map(s=>({...s,status:'not-checked',lastAttemptAt:null,lastSuccessfulAt:null,count:0,error:null}));
 f.items=[{id:'official:'+'a'.repeat(32),companyId:'candidate-nebius',ticker:'NBIS',title:'Nebius reports financial results',url:'https://nebius.com/newsroom/test-results',sourceId:'nbis-news',kind:'results',publishedDate:null,collectedAt:stamp,lastSeenAt:stamp,metadataStatus:'index-link',metadataCheckedAt:null,metadataError:null,contentScope:'metadata-only'}] as typeof f.items;
 return f;
}
it('validates the actual persisted official snapshot',()=>{expect(parseOfficialSnapshot(initial).version).toBe(1);});
it('rejects wrong company, off-domain links, duplicate identities and false successful sources',()=>{
 for(const change of [
  (f:any)=>f.items[0].companyId='candidate-iren',
  (f:any)=>f.items[0].url='https://evil.test/newsroom/a',
  (f:any)=>f.items.push(f.items[0]),
  (f:any)=>f.sources[0].status='ok',
  (f:any)=>f.sources.pop(),
 ]){const f=fixture();change(f);expect(()=>parseOfficialSnapshot(f)).toThrow();}
});
it('keeps unknown dates, provenance and source limitations in the research pack',()=>{
 const f=parseOfficialSnapshot(fixture());const pack=officialPack('NBIS',f);
 expect(pack).toContain('תוכן המסמכים לא נקרא');expect(pack).toContain('לא זמין — אין להסיק ממועד האיסוף');
 expect(pack).toContain('https://nebius.com/newsroom/test-results');expect(pack).toContain('מה השתנה בהכנסות בפועל');
 expect(officialPack('DLO',f)).not.toContain('test-results');expect(officialPack('DLO',f)).toContain('TPV');
});
it('previews a company-specific pack and reports missing dates honestly',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>fixture()}));const prepare=vi.fn();
 render(<OfficialSources ticker="NBIS" onPrepare={prepare}/>);
 await screen.findByText('Nebius reports financial results ↗');
 expect(screen.getByText(/תאריך לא זמין במטא־נתונים/)).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'הכנת חבילת מקורות ל־NBIS'}));expect(prepare.mock.calls[0][0]).toContain('NBIS');
 fireEvent.click(screen.getByRole('button',{name:/^DLO$/}));
 fireEvent.click(screen.getByRole('button',{name:'הכנת חבילת מקורות ל־DLO'}));expect(prepare.mock.calls[1][0]).toContain('TPV');
});
it('retains prior items after a refresh fails',async()=>{
 const request=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>fixture()}).mockRejectedValueOnce(Error('offline'));
 vi.stubGlobal('fetch',request);render(<OfficialSources onPrepare={()=>{}}/>);
 await screen.findByText('Nebius reports financial results ↗');
 fireEvent.click(screen.getByRole('button',{name:'רענון המקורות'}));await screen.findByRole('status');
 expect(screen.getByText('Nebius reports financial results ↗')).toBeTruthy();
});
