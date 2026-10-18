// Shared browser/Actions semantic validation, after the JSON schema check.
export function validateDiscovery(feed) {
  if (!feed.discovery && !feed.articles) return;
  const d = feed.discovery;
  if (!d || !Array.isArray(feed.articles)) throw Error('Incomplete discovery snapshot');
  const companies = new Map(d.registry.companies.map(c => [c.id, c]));
  if (companies.size !== d.registry.companies.length) throw Error('Duplicate company');
  const providers = new Map(d.registry.providers.map(p => [p.id, p]));
  const expected = [...providers.values()].filter(p => p.enabled).length * companies.size;
  const statuses = new Set();
  for (const s of d.sources) {
    const key = s.provider + ':' + s.securityId;
    const u = new URL(s.queryUrl);
    if (!companies.has(s.securityId) || !providers.get(s.provider)?.enabled || statuses.has(key)
        || u.protocol !== 'https:' || u.username || u.password || u.port
        || !(s.provider === 'google-news' ? u.hostname === 'news.google.com' && u.pathname === '/rss/search'
            : u.hostname === 'api.gdeltproject.org' && u.pathname === '/api/v2/doc/doc')) throw Error('Wrong discovery source');
    if ((s.status === 'results') !== (s.count > 0) || (s.status !== 'failed' && s.lastSuccessfulAt !== s.lastAttemptAt)) throw Error('False provider status');
    statuses.add(key);
  }
  if (statuses.size !== expected) throw Error('Missing discovery statuses');
  const all = d.sources.length > 0 && d.sources.every(s => s.status !== 'failed');
  const working = d.sources.some(s => s.status !== 'failed');
  if ((d.status === 'complete') !== all || (d.status === 'failed') === working
      || (!all && d.lastSuccessfulAt === d.lastAttemptAt)
      || (d.noNewItems && (!working || d.newCount !== 0))) throw Error('False discovery success');
  const ids = new Set();
  for (const n of feed.articles) {
    const c = companies.get(n.securityId), p = providers.get(n.discoveryProvider), u = new URL(n.sourceUrl);
    if (!c || !p || ids.has(n.id) || n.company !== c.name || n.ticker !== c.displayTicker
        || n.sourceId !== n.discoveryProvider + ':' + c.id || n.id !== 'article:' + n.documentId
        || n.originalTitle !== n.headline || n.summary !== '' || !d.seenIds.includes(n.id)
        || u.protocol !== 'https:' || u.username || u.password || u.port
        || (n.discoveryProvider === 'google-news' && (u.hostname !== 'news.google.com' || !u.pathname.startsWith('/rss/articles/') || n.linkKind !== 'google-news-redirect'))
        || (n.discoveryProvider === 'gdelt' && (n.linkKind !== 'publisher' || n.publishedAt !== null))) throw Error('Wrong article attribution');
    const norm = x => ' ' + x.toLowerCase().replace(/[^a-z0-9\u0590-\u05ff]+/g,' ').trim() + ' ';
    const has = term => norm(n.headline).includes(norm(term));
    if (c.exclude.some(has) || !(c.distinctiveAliases.some(has) || (c.aliases.some(has) && c.context.some(has)))) throw Error('Wrong company headline');
    ids.add(n.id);
  }
}
