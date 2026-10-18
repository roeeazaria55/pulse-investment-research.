# PULSE — Investment Research

A Hebrew, RTL, mobile-first investment research PWA. Built with React, Vite, TypeScript and Tailwind CSS. Runs entirely in the browser. No backend, credentials, paid services, tracking, or market-data API.

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

`public/data/feed.json` contains **three fictional, clearly labeled examples**, each linked to an `example.com` placeholder. They do not claim any company event happened. The briefing is a template, not an automated research report. No live prices, financial metrics, performance charts or implied market updates are shown.

`updatedAt: null` means there has never been a successful real ingestion. A demo feed is always stale; a real feed older than 18 hours is stale. Refreshing the app or successfully downloading a demo does not advance the data timestamp. Fetch failures leave the last valid in-memory feed visible; offline loads use the service-worker cache. Publication/collection times remain the source's recorded values. Cached real data retains its original `updatedAt` and freshness warning.

## GitHub Pages deployment

1. Push this project to `main` in `roeeazaria55/pulse-investment-research.` (the trailing period is part of the supplied repository name).
2. In the repository, choose **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Open **Actions → Deploy PULSE to GitHub Pages** and run it, or push a commit to `main`.
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

## Intentionally unfinished / Phase 2

No crawler, live quotes, AI summarization service, verified market ticker/exchange mapping, real financial data, generated morning/evening briefings, scheduled ingestion, authentication, cloud sync or broker integration. The schema and deployment path support a future twice-daily GitHub Actions publisher. Before enabling it, verify every security's current exchange, symbol and share class, select permitted sources and maintain provenance. There is no investment recommendation engine.
