import {describe,it,expect} from 'vitest';
import {validateIntelligence} from '../src/data/intelligenceValidation.mjs';

const company='candidate-nebius';
const makeFeed=(b)=>({
  news:[],articles:[],discovery:{registry:{companies:[{id:company}]}},
  intelligence:{ratings:{},eventGroups:[],calendar:{events:[
    {securityId:company,status:'unannounced',date:null,time:null,timeZone:null}
  ]},dailyBriefings:[{...b,companies:[{securityId:company,facts:[]}]}]}
});
const morning={
  id:'briefing:2026-10-28:08',date:'2026-10-28',scheduledLocalTime:'08:00',
  startAt:'2026-10-27T17:00:00+00:00',endAt:'2026-10-28T06:00:00+00:00',
  generatedAt:'2026-10-28T14:27:40+00:00'
};
describe('Jerusalem briefing validation',()=>{
  it('accepts production morning/evening slots and previous 13:00 daily archive',()=>{
    expect(()=>validateIntelligence(makeFeed(morning))).not.toThrow();
    expect(()=>validateIntelligence(makeFeed({
      ...morning,id:'briefing:2026-10-28:19',scheduledLocalTime:'19:00',
      startAt:'2026-10-28T06:00:00+00:00',endAt:'2026-10-28T17:00:00+00:00',
      generatedAt:'2026-10-28T18:00:00+00:00'
    }))).not.toThrow();
    expect(()=>validateIntelligence(makeFeed({
      ...morning,id:'daily:2026-10-28',scheduledLocalTime:'13:00',
      startAt:'2026-10-27T11:00:00+00:00',endAt:'2026-10-28T11:00:00+00:00'
    }))).not.toThrow();
  });
  it('handles DST entry and exit without assuming 24 elapsed hours',()=>{
    expect(()=>validateIntelligence(makeFeed({
      ...morning,id:'briefing:2026-03-27:08',date:'2026-03-27',
      startAt:'2026-03-26T17:00:00+00:00',endAt:'2026-03-27T05:00:00+00:00'
    }))).not.toThrow();
    expect(()=>validateIntelligence(makeFeed({
      ...morning,id:'briefing:2026-10-25:08',date:'2026-10-25',
      startAt:'2026-10-24T16:00:00+00:00',endAt:'2026-10-25T06:00:00+00:00'
    }))).not.toThrow();
  });
  it('rejects fake slot identity, invalid start and time mismatch',()=>{
    expect(()=>validateIntelligence(makeFeed({...morning,id:'daily:2026-10-28'}))).toThrow();
    expect(()=>validateIntelligence(makeFeed({...morning,startAt:'2026-10-27T18:00:00+00:00'}))).toThrow();
    expect(()=>validateIntelligence(makeFeed({...morning,endAt:'2026-10-28T07:00:00+00:00'}))).toThrow();
    expect(()=>validateIntelligence(makeFeed({...morning,generatedAt:'2026-10-27T00:00:00+00:00'}))).toThrow();
    expect(()=>validateIntelligence(makeFeed({...morning,scheduledLocalTime:'15:00'}))).toThrow();
  });
  it('keeps fact timestamps within the exact validated slot',()=>{
    const feed=makeFeed(morning);
    feed.intelligence.dailyBriefings[0].companies[0].facts=[{publishedAt:morning.endAt}];
    expect(()=>validateIntelligence(feed)).toThrow('Item outside daily window');
  });
});
