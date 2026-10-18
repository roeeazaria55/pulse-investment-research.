# PULSE — Investment Research

A Hebrew, RTL, mobile-first investment research PWA. Built with React, Vite, TypeScript and Tailwind CSS. Runs entirely in the browser. No backend, credentials, paid services, tracking, or market-data API.

**Phase 2 news discovery:** public company headlines are collected through Google News RSS in GitHub Actions, with SEC metadata as a separate supplemental source. The Nebius feasibility run returned real titles; GDELT returned HTTP 429 and remains disabled. See [news discovery, source limitations and data contract](docs/NEWS-DISCOVERY.md), [supplemental SEC guide](docs/phase-2.md), [feed schema](schemas/feed-v2.schema.json) and [headline extension schema](schemas/discovery.schema.json). Deployed per-company/provider status determines current coverage. Company identity for search is independent of stock-listing/CIK verification. No AI summaries or full article text are collected.

The standard Ubuntu Actions runner supplies Python 3 and Jerusalem timezone data. Local parser checks: `python3 -m unittest discover -s scripts -p 'test_articles.py'`. Headline collection: `python3 scripts/collect_articles.py` followed by `npm run collect`; only public metadata is accessed. Do not substitute private watchlists for the public search registry.

## Run locally

Use Node.js 22.22.2+, Node 24.15+, or Node 26+.

```sh
npm ci
npm run dev
```

```sh
npm run typecheck
npm test
npm run build
npm run preview
```

The runner configuration loader avoids config bundling restrictions in locked-down Windows environments. The lockfile pins the tested dependency tree.

## Included in v1

- Home: demo briefing, important demo news, research attention items, watchlist summary, real-data freshness state.
- Portfolio: create, edit and remove holdings, manually entered allocation, average cost, currency, thesis and risk notes. Starts empty. Total entered allocation cannot exceed 100%.
- News: search, importance filters, saved items, publication and collection timestamps, explicit demonstration labels and source links.
- Research: per-company editable thesis, revenue, profitability, cash flow, valuation, competitive advantages, catalysts, risks, Bear/Base/Bull cases and dated research history.
- ChatGPT: editable Hebrew prompt with research, relevant news, dates and source URLs; clipboard copy with fallback/manual selection; a separate ChatGPT link. The link sends no local data. The user chooses what to paste.
- Watchlist: all eleven requested provisional companies; add/edit/remove/categorize/search/filter. Not treated as holdings. All ticker mappings remain unverified; the four named Israeli companies deliberately have no assumed ticker.
- PWA: standalone manifest, 192/512 PNG icons, maskable icon, Apple touch icon, scoped service worker, offline application shell and cached public feed, Android install prompt and iPhone guidance.
- Accessible navigation with current-page state, keyboard focus styles, skip link, labeled inputs, status announcements, reduced motion support and responsive bottom navigation.
- Private JSON backup export from the desktop sidebar and mobile install/help dialog. Keep backups private. Restore/import is not included in v1.

## Privacy and local data

Personal data lives under `pulse.personal.v1` in **localStorage**, only on this browser and origin. Public JSON never includes holdings, allocation, purchase prices, private thesis, risk notes, personal research, saved-item preferences or watchlist customizations. Research overrides are saved locally; default public research can be supplied separately. Removing a security preserves its research. Browser storage is not encrypted; clearing site data, switching origins/browsers, or uninstalling can remove access. Export before making those changes. There is no cross-device sync.

Invalid or blocked storage produces an explicit error. A failed write is not reported as saved. Corrupt raw data can be exported for recovery. Research edits are saved when navigating within the app; explicit save is available, and leaving with unsaved edits raises the browser's standard warning where supported. Do not place personal backups in this repository.

## Data honesty and freshness

Before first collection `public/data/feed.json` can contain three explicitly fictional v1 examples. The first Phase 2 attempt replaces them with a v2 feed containing only validated SEC metadata (or an honest empty/failed status). Tests keep the v1 demo fixture separately under `tests/fixtures`. No live prices, fabricated metrics or AI research are shown. V2 titles remain source-original; briefings use disclosed rule templates.

In v2, `lastAttemptAt` is separate from each source's `lastSuccessfulAt`. Global `lastSuccessfulAt` and legacy `updatedAt` are reserved for full registry coverage; they stay null while eight companies are uncovered, even if the three configured sources work. Source-level timestamps drive age warnings (18 hours); partial failures never refresh failed sources. Fetch failures leave the last valid in-memory feed visible; offline loads use the cached public feed. Missing publication times stay null. See the Phase 2 guide for exact semantics.

## GitHub Pages deployment

1. Push this project to `main` in `roeeazaria55/pulse-investment-research.` (the trailing period is part of the supplied repository name).
2. In the repository, choose **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Open **Actions → Publish PULSE → Run workflow → main**, or push a code commit to `main`.
4. The workflow installs locked dependencies, runs tests, builds, uploads `dist`, then deploys through the Pages environment. The deployment job returns the actual site URL. Pages must be available for the repository/account plan.

The workflow derives `VITE_BASE_PATH` from `github.event.repository.name`, including the trailing period. All JS, CSS, manifest, icon, service worker and data URLs respect that path. For a custom-domain/root site, change the build environment value to `/`. For a manual subpath build:

```powershell
$env:VITE_BASE_PATH='/pulse-investment-research./'
npm run build
npm run preview
# Open http://127.0.0.1:4173/pulse-investment-research./
```

Do not upload `node_modules`, private backups, `.env` files or the user's browser storage. `dist` is generated, not committed. The first workflow deploys automatically only after Pages is enabled; this repository includes configuration, not a claim of a live deployment.

## Install on a phone

Visit the deployed HTTPS URL once with a connection. On iPhone use Safari → Share → Add to Home Screen. On Android use Chrome → menu → Install app / Add to Home screen, or the in-app download button when the browser offers installation. Open the icon to run standalone. First successful loading installs and caches the shell, its hashed JS/CSS and the public feed. Then test in airplane mode. Installation requires supported browser settings and available local storage. Localhost supports desktop development; an HTTP LAN address is not a valid phone installation test.

`public/sw.js` uses a scope-specific cache. Feed requests are network-first with cache fallback, while the app shell is cached for offline use. Bump the service worker `VERSION` for each shell release. A new install preloads the current hashed assets before taking over; it never deletes another app scope's cache. Browser checks: Application → Manifest (icons, standalone start URL) and Service workers (activated worker and matching scope), then switch offline and reload. A physical iOS/Android install still needs device verification.

## Architecture

```text
src/data/          Public ingestion validation, staleness, provisional list
src/state/         Versioned local personal storage and validation
src/research/      Hebrew prompt construction and clipboard behavior
src/components/    Shared presentation elements
src/App.tsx        Screen composition and user actions
public/data/       Public-only static feed
schemas/           Documented JSON Schema contract
docs/              Phase 2 ingestion plan
tests/             Contract, storage, research and UI behavior checks
```

The public format is documented by [feed.schema.json](schemas/feed.schema.json) and [the ingestion plan](docs/data-contract.md). Public research and local research are separate: editing a public profile creates a private local override.

## Remaining scope

The scoped SEC filings collector, persisted deduplication, rule-template briefings and morning/evening schedule are implemented by `Publish PULSE`. Availability must be confirmed by an actual manual run and the published source statuses. Eight registry companies await reviewed mappings/sources. No live quotes, article crawler, IR/RSS ingestion, AI summarization, financial metric extraction, authentication, cloud sync, private-data ingestion or broker integration is included. The application is not an investment recommendation engine.
