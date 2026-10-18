// @vitest-environment jsdom
import React from 'react';
import {it,expect,afterEach} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import registry from '../public/data/registry.json';
import searchRegistry from '../public/data/news-registry.json';
import {collect} from '../scripts/ingest/engine.mjs';
import {parseV2,resolveSecurity} from '../src/data/feedV2';
import {NewsCard} from '../src/components/UI';
import {WebNewsSearch} from '../src/components/Discovery';
const now='2026-10-18T12:00:00+00:00';
async function fixture(){
  const {feed}=await collect({registry,now,getJson:async()=>{throw Error('blocked');}});
  const c=searchRegistry.companies[0],id='a'.repeat(32);
  const article={id:'article:'+id,documentId:id,securityId:c.id,ticker:c.displayTicker,company:c.name,headline:'Nebius AI cloud test fixture',originalTitle:'Nebius AI cloud test fixture',sourceUrl:'https://news.google.com/rss/articles/test',publisher:'Test Publisher',sourceName:'Test Publisher',sourceId:'google-news:'+c.id,discoveryProvider:'google-news',linkKind:'google-news-redirect',publishedAt:null,discoveredAt:null,collectedAt:now,importance:'low',classification:{rule:'company-headline-match',reason:'Test fixture only'},summary:'',summaryKind:'metadata-only',demo:false};
  feed.articles=[article];
  feed.discovery={version:1,registry:searchRegistry,lastAttemptAt:now,lastSuccessfulAt:now,status:'complete',newCount:1,noNewItems:false,seenIds:[article.id],briefings:[],sources:searchRegistry.companies.map((company,i)=>({provider:'google-news',securityId:company.id,name:company.name,queryUrl:'https://news.google.com/rss/search?q=test',lastAttemptAt:now,lastSuccessfulAt:now,status:i?'zero-results':'results',error:null,count:i?0:1,newCount:i?0:1,rejectedCount:0}))};
  return feed;
}
afterEach(()=>{cleanup();localStorage.clear();});
it('validates and merges articles independently of blocked SEC and unverified listing',async()=>{
  const f=await fixture();
  const parsed=parseV2(f);expect(parsed.news).toHaveLength(1);
  expect(resolveSecurity(parsed,{name:'Nebius',ticker:'NBIS'}).id).toBe('candidate-nebius');
  expect(resolveSecurity(parsed,{name:'Gilat Satellite Networks',ticker:'GILT'})).toBeUndefined();
});
it('rejects wrong attribution, duplicate, malicious link and false full success',async()=>{
  for(const mutate of [f=>f.articles[0].company='Gilat',f=>f.articles.push(f.articles[0]),f=>f.articles[0].sourceUrl='https://evil.test/a',f=>f.discovery.sources[0].status='failed']){
    const f=await fixture();mutate(f);expect(()=>parseV2(f)).toThrow();
  }
});
it('labels Google links, missing date, metadata limits and keeps unrelated reports local',async()=>{
  const f=await fixture();render(React.createElement(NewsCard,{item:f.articles[0],saved:false,onSave:()=>{},onResearch:()=>{}}));
  expect(screen.getByRole('link',{name:/פתיחה דרך Google News/}).getAttribute('href')).toContain('news.google.com');
  expect(screen.getByText(/לא נמסר במקור/)).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'דיווח: לא קשור לחברה'}));
  expect(JSON.parse(localStorage.getItem('pulse-unrelated-news'))).toEqual([f.articles[0].id]);
});
it('offers disambiguated web search even with no public feed',()=>{
  render(React.createElement(WebNewsSearch,{name:'Gilat Telecom'}));
  const href=decodeURIComponent(screen.getByRole('link').getAttribute('href'));
  expect(href).toContain('Gilat Telecom');expect(href).toContain('-"Gilat Satellite Networks"');
});
