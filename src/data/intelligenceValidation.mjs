export function validateIntelligence(feed){
  const x=feed.intelligence;if(!x)return;
  const news=[...feed.news,...(feed.articles||[])],ids=new Set(news.map(n=>n.id));
  const companies=new Set(feed.discovery?.registry.companies.map(c=>c.id));
  if(new Set(x.dailyBriefings.map(b=>b.id)).size!==x.dailyBriefings.length)throw Error('Duplicate daily publication');
  if(!companies.size)throw Error('Intelligence needs discovery registry');
  for(const n of news){
    const r=x.ratings[n.id];if(!r || r.version!==x.ratingVersion || r.evidenceUrls[0]!==n.sourceUrl)throw Error('Missing rating provenance');
    if(r.level==='high'&&(!r.verifiedOfficial||r.basis==='headline-only'||r.companyRelevance==='rejected'||r.eventKind==='opinion'))throw Error('Unsupported high importance');
    if(r.verifiedOfficial&&!n.sourceId?.startsWith('sec-'))throw Error('A headline cannot claim official verification');
    if(n.importance!==r.level)throw Error('Rating mismatch');
  }
  for(const g of x.eventGroups)if(!companies.has(g.securityId)||g.itemIds.some(id=>!ids.has(id)))throw Error('Wrong event association');
  if(new Set(x.calendar.events.map(e=>e.securityId)).size!==companies.size)throw Error('Missing calendar coverage');
  for(const e of x.calendar.events){if(!companies.has(e.securityId)||e.status==='confirmed'&&(!e.date||!e.sourceUrl||!e.verifiedAt)||e.status==='unannounced'&&e.date!==null||e.time&&!e.timeZone)throw Error('Invalid earnings evidence');}
  for(const b of x.dailyBriefings){
    if(Date.parse(b.endAt)-Date.parse(b.startAt)!==86400000)throw Error('Daily window must be 24 elapsed hours');
    const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',hour:'2-digit',hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(b.endAt));
    const p=Object.fromEntries(parts.map(v=>[v.type,v.value]));
    if(p.hour!=='13'||`${p.year}-${p.month}-${p.day}`!==b.date||b.id!==`daily:${b.date}`||Date.parse(b.generatedAt)<Date.parse(b.endAt))throw Error('Wrong daily boundary');
    for(const c of b.companies){if(!companies.has(c.securityId))throw Error('Wrong briefing company');for(const f of c.facts){if(!f.publishedAt||Date.parse(f.publishedAt)<Date.parse(b.startAt)||Date.parse(f.publishedAt)>=Date.parse(b.endAt))throw Error('Item outside daily window');}}
  }
}
