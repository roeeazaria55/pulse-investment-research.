import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { validateFeed, validatePersistedFeed } from '../scripts/ingest/validate.mjs';

// Exercise the production snapshot shape, including discovery, calendar,
// retained daily publications and source provenance, rather than a reduced mock.
const snapshot = JSON.parse(readFileSync(new URL('../public/data/feed.json', import.meta.url), 'utf8'));
function priorSnapshot() {
  const feed = structuredClone(snapshot);
  feed.intelligence.ratingVersion = 'evidence-3.1';
  for (const rating of Object.values(feed.intelligence.ratings)) rating.version = 'evidence-3.1';
  return feed;
}
describe('persisted rating version transition', () => {
  it('reads the prior supported format without changing ratings, IDs or publication history', () => {
    const prior = priorSnapshot(), unchanged = structuredClone(prior);
    expect(validatePersistedFeed(prior)).toBe(true);
    expect(prior).toEqual(unchanged);
    expect(() => validateFeed(prior)).toThrow('Invalid feed');
  });
  it('continues to reject corrupt prior source attribution and rating evidence', () => {
    for (const corrupt of [
      f => { f.articles[0].company = 'Another company'; },
      f => { f.intelligence.ratings[f.articles[0].id].evidenceUrls = ['https://example.com/wrong']; },
      f => { f.intelligence.ratings[f.articles[0].id].version = 'evidence-3.2'; },
      f => { f.intelligence.ratingVersion = 'evidence-unknown'; },
    ]) {
      const prior = priorSnapshot(); corrupt(prior);
      expect(() => validatePersistedFeed(prior)).toThrow();
    }
  });
  it('accepts current output only when every retained item has a current rating', () => {
    const feed = priorSnapshot();
    feed.intelligence.ratingVersion = 'evidence-3.2';
    for (const rating of Object.values(feed.intelligence.ratings)) rating.version = 'evidence-3.2';
    expect(validateFeed(feed)).toBe(true);
    delete feed.intelligence.ratings[feed.articles[0].id];
    expect(() => validateFeed(feed)).toThrow('Missing rating provenance');
  });
});
