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
    // Historical daily: 13:00–13:00, fixed elapsed 24h.
    // New briefings: previous local 19:00 → 08:00 or 08:00 → 19:00.
    // Neither new window has a fixed UTC duration across Israeli DST shifts.
    const start=Date.parse(b.startAt),end=Date.parse(b.endAt),generated=Date.parse(b.generatedAt);
    if(![start,end,generated].every(Number.isFinite)||start>=end||generated<end)throw Error('Invalid briefing timestamps');
    const local=(timestamp)=>{
      const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Jerusalem',
        hour:'2-digit',minute:'2-digit',hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit'
      }).formatToParts(new Date(timestamp));
      const p=Object.fromEntries(parts.map(v=>[v.type,v.value]));
      return {date:`${p.year}-${p.month}-${p.day}`,time:`${p.hour}:${p.minute}`};
    };
    const actualEnd=local(end);
    if(actualEnd.date!==b.date||actualEnd.time!==b.scheduledLocalTime)throw Error('Wrong briefing local end');
    if(b.scheduledLocalTime==='13:00'){
      if(b.id!==`daily:${b.date}`||end-start!==86400000)throw Error('Invalid legacy daily boundary');
    }else if(b.scheduledLocalTime==='08:00'||b.scheduledLocalTime==='19:00'){
      const hour=b.scheduledLocalTime.slice(0,2);
      if(b.id!==`briefing:${b.date}:${hour}`)throw Error('Wrong briefing identity');
      const previousDay=new Date(b.date+'T12:00:00Z');
      previousDay.setUTCDate(previousDay.getUTCDate()-1);
      const expectedStart=b.scheduledLocalTime==='08:00'
        ? {date:previousDay.toISOString().slice(0,10),time:'19:00'}
        : {date:b.date,time:'08:00'};
      const actualStart=local(start);
      if(actualStart.date!==expectedStart.date||actualStart.time!==expectedStart.time)
        throw Error('Wrong briefing local start');
    }else throw Error('Unsupported briefing time');
    for(const c of b.companies){if(!companies.has(c.securityId))throw Error('Wrong briefing company');for(const f of c.facts){if(!f.publishedAt||Date.parse(f.publishedAt)<Date.parse(b.startAt)||Date.parse(f.publishedAt)>=Date.parse(b.endAt))throw Error('Item outside daily window');}}
  }
}
