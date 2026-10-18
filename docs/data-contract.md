# Public data contract and future ingestion

`public/data/feed.json` implements `schemas/feed.schema.json` (JSON Schema draft-07). It must contain only public, independently sourced information. Never copy localStorage or private backups into it.

## Envelope

| Field       | Meaning                                                                              |
| ----------- | ------------------------------------------------------------------------------------ |
| `version`   | Literal `1`; change version for breaking migrations                                  |
| `updatedAt` | ISO 8601 UTC time of the last successful complete ingestion; `null` until one exists |
| `demo`      | Boolean; `true` for demonstration data                                               |
| `news`      | Array of news items                                                                  |
| `research`  | Array of public research profiles                                                    |

News requires `id`, `ticker`, `company`, `headline`, `sourceUrl`, `publishedAt`, `collectedAt`, `importance`, `summary`, `demo`. Importance is `high`, `medium`, or `low`. IDs must be stable and unique to avoid duplicate saved articles. Use canonical HTTP(S) source URLs. Keep publication and collection dates distinct. Summaries must be factual, attributed to their sources and checked before publication. Do not create facts to fill gaps.

Research requires `ticker`, `company`, `updatedAt`, `sourceUrls`, `content`, `demo`. `content` requires these string fields (empty means unknown): `thesis`, `revenue`, `profitability`, `cashFlow`, `valuation`, `advantages`, `catalysts`, `risks`, `bear`, `base`, `bull`. `notes` is an array of `{ id, createdAt, text }` with ISO 8601 UTC timestamps. Public research should distinguish sourced facts from scenarios and author assumptions. All URLs must use HTTP(S).

If envelope `demo` is `false`, no news/research item can have `demo: true`, and `updatedAt` must be non-null. The application rejects invalid structures and dangerous URL protocols before rendering. Schema validation belongs in future ingestion too. The service worker performs minimal envelope checks before caching; the application performs full field validation before displaying cached or fetched data.

## Planned twice-daily GitHub Actions job (not enabled)

1. Configure a future schedule such as `0 5,17 * * *` (UTC; Israel local time varies with daylight saving). Scheduled jobs can be delayed by GitHub and are not a market-time guarantee.
2. Read a curated **public** security registry with verified symbol, exchange, share class and verification source/date. The current provisional list is not sufficient. Do not reuse a private portfolio as the registry.
3. Collect approved public sources under their rate limits and terms. Deduplicate stable IDs; preserve the original URL and actual publication time. Do not treat collection time as publication time.
4. Produce news and separately sourced research; keep missing metrics empty. Update `updatedAt` only after the complete validation succeeds. On source/validation failure preserve the previous feed and surface the workflow error.
5. Validate against the schema and the ingestion rules. Write an atomic replacement to `public/data/feed.json`; commit only changed public output through a scoped workflow token. Never add API keys or local financial information.
6. Trigger the Pages deployment explicitly from that workflow (for example by calling a reusable deployment workflow). Commits made with `GITHUB_TOKEN` do not normally trigger another push workflow. Do not rely on a generated commit to start `pages.yml` automatically.
7. Run tests/build and deploy. Cached clients fetch data network-first, retain original timestamps offline and mark real updates older than 18 hours stale.

This phase-one repository deliberately has no scheduled crawler or paid AI/data service. No market mapping is asserted to be verified.
