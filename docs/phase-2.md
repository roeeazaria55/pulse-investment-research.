# Phase 2: public filings ingestion

This guide describes the supplemental SEC collector. For the current public
headline search, independently reviewed company identities and actual provider
proof, see [News discovery](NEWS-DISCOVERY.md). "Without coverage" below refers
only to SEC coverage, not to the independent company news search.

## Scope and identity

The checked-in `public/data/registry.json` is a **public research universe**, independent of the user's local watchlist. Stable IDs identify a specific selected listing/class, not a display name or a ticker alone. Each record carries name, ticker, venue, CIK if verified, share class, aliases, verification evidence/date and an explicit source or `null`.

Initial reviewed securities are META Class A / Nasdaq / CIK 1326801, DLO Class A / Nasdaq / CIK 1846832 and LMND common stock / NYSE / CIK 1691421. Evidence is linked directly to issuer filing covers/security descriptions, reviewed on 2026-10-18. Before accepting any source response, every run rechecks the exact CIK, a curated legal name and the aligned ticker/exchange pair. Aliases are for display/local matching, never fuzzy source attribution. A mismatch fails the whole source and retains old valid data. The mapping file alone is not a guarantee of current accuracy; changed names/listings require review.

NBIS, FTAI, SNDK, IREN, Next Vision, Enlight, BrainsWay and Gilat Telecom deliberately remain unverified and **without coverage**. No speculative CIK or exchange is assigned. In particular Gilat Telecom is not assumed to be GILT; BrainsWay ordinary shares and depositary securities, and Enlight dual listings, are not silently merged. Adding a verified venue/class requires a reviewed source and registry edit, not a private watchlist change.

## Enabled source family and reuse

Only the official SEC `https://data.sec.gov/submissions/CIK##########.json` family is enabled. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) explicitly describes public, keyless submissions access. [Fair access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) requires declared automated access and rate moderation (SEC maximum 10 requests/second). The implementation uses one request at a time, at least 1.1 seconds apart; declares PULSE and its public repository issue page as administrative contact. An optional repository variable `SEC_USER_AGENT` can supply the operator's actual SEC-compliant contact identity. It is not an API key. Do not impersonate a browser or rotate identities to evade a block. A local 403 was observed during development and not bypassed. The deployed status, not the existence of this code, determines which sources work from Actions.

No IR/RSS source has been enabled: none has completed the separate availability, entity attribution, terms/reuse and redirect review. Do not add scraped articles or proxy fallback URLs merely to obtain coverage. No paywall or robots restriction is bypassed. This stage is a **filings monitor**, not a comprehensive commercial-news feed.

Only metadata is collected; filing/article bodies are not downloaded. `primaryDocDescription` remains the original English title (including original case); if absent, the exact SEC `form` string is used and `titleOrigin` records this fallback. `originalTitle` is retained. Hebrew summaries state only form, filing date when present and accession ID, and attribute SEC EDGAR. No reproduced article, copyrighted abstract, sentiment analysis, financial conclusion or AI-generated analysis is claimed. Importance is explained by form rules (`10-K/10-Q/20-F/40-F`: high, `8-K/6-K`: medium, others low, including amendments) and is **not a buy recommendation**.

## Network and data limits

Collection runs only in Actions, never from the browser. A client limits each request including streamed body to 15 seconds, three attempts maximum for timeout/network/429/5xx with 1/2 second backoff, 2 MiB decompressed body, at most two redirects. Every redirect is rechecked against the exact HTTPS host/path allowlist. Credentials, custom ports, queries, fragments, IP hosts and cross-host redirects are rejected. 401/403/451 stop immediately without retries or alternative endpoints. JSON content type, size, structure and all aligned filing columns are validated. At most 10,000 recent rows are considered; the SEC recent API generally supplies about 1,000. Historical archive chunks are not crawled. Filenames are restricted to safe path segments. Nothing fetched is executed as a command, script, path, HTML or workflow expression.

`documentId` is the accession number. Stable deduplication uses **CIK + accession**, not headline, collection time or symbol. Insider filing accession prefixes may identify a submitting person, so they are not misused as the issuer CIK. First collection bootstraps up to 30 filings per source from the preceding 30 days (or rows with unknown date), explicitly labeled as initialization. All rows in that initial response are recorded as seen, so old archive entries do not later become new. Later successful collections add only unseen IDs. The feed retains the 600 latest records; state retains seen IDs separately and aborts above 100,000 pending a reviewed retention migration. Existing first-collection timestamps survive deduplication.

`publishedAt` is the actual zoned SEC `acceptanceDateTime`, or **null** if absent/unusable. `publicationTimeBasis` explains it. A separate `filingDate` is a date only; it is never converted into a made-up midnight timestamp. `collectedAt` is actual UTC collection time. Acceptance time is labeled as SEC acceptance/publication metadata, not guaranteed public dissemination time.

## Contract v2 and failures

`schemas/feed-v2.schema.json` documents v2. `scripts/ingest/make-schema.mjs` regenerates it. The application still reads v1 demonstration fixtures; v2 public feeds contain no demonstration articles. Source schema and provenance validation are run before any write/build. V2 public research is empty: no financial metrics or AI research have been fabricated.

- `lastAttemptAt`: time of this attempt, even if sources fail.
- Per-source `lastSuccessfulAt`: updated only after a valid identity and complete source parse.
- Global `lastSuccessfulAt`/legacy `updatedAt`: updated **only when every registry record has working verified coverage**. With the initial eight uncovered companies this remains null. A partially successful collection is never presented as full success.
- `status`: complete / partial / failed / no-coverage; `sources` distinguishes ok, blocked, error, identity-mismatch, no-source, preserving prior source successes.
- `noNewItems` means zero newly collected IDs **in successfully checked sources**. It is false if none succeeded, and is never a statement about uncovered/failed companies.
- On a failed source, old valid items and their original timestamps remain. Invalid persisted v2 feed/state aborts publication rather than resetting history or replacing the feed with empty success.

The UI shows successful coverage count, every uncovered company, source failures, last attempts, last source successes and overall full-success time. Data older than 18 hours is marked stale. A recent partial failure still shows the error; it does not refresh the old source's age. Source details include verification evidence and the Actions run URL.

The browser's static feed request uses a public schema/version and minute bucket to avoid a preceding Pages deployment's CDN response. The service worker stores one canonical feed snapshot rather than accumulating per-query cache entries. This request contains no personal security list. GitHub Actions summaries also show collection health independently of the green test/deployment result.

### First production check, 2026-10-18

[Manual run 39126167218](https://github.com/roeeazaria55/pulse-investment-research./actions/runs/39126167218) passed validation, 36 tests, build, selected-file persistence and deployment. The actual public payload reported **0/11 working coverage**, all three SEC endpoints blocked, no invented items and `lastSuccessfulAt: null`. This verifies failure handling/publication, **not an active news scanner**. The official Meta IR RSS discovery page was reviewed; an availability probe of its advertised feed also returned 403, so no RSS source was enabled. No access restriction was bypassed. A later working-source claim requires a new successful ingestion and published status.

## Morning/evening briefings and scheduling

Briefings are deterministic Hebrew templates with original filing title, source link, classification reason and questions to check. `kind: rule-template` explicitly excludes AI. IDs are the **Asia/Jerusalem local date + morning/evening**, with `Intl` resolving DST. Same-period retries merge IDs without duplication. On a new period, already-seen reports are not repeated. If no source succeeds, the briefing says collection failed instead of claiming there were no new filings. 28 briefings are retained (UI displays latest plus four history entries).

UTC cron `23 4,5,16,17 * * *` supplies winter/summer alternatives for approximately **07:23 and 19:23 Israel time**. The collector accepts scheduled arrivals within local 07–10 or 19–22 windows, and `completedSlots` skips the redundant DST alternative after all configured sources succeeded (unverified records still show no coverage). Failed sources allow the next eligible run to retry. Manual runs and push runs bypass the schedule gate. GitHub schedules use the default branch, can be delayed/dropped, and public-repository scheduled workflows can be disabled after 60 days without activity. There is no guaranteed delivery time or automatic backfill of missed morning reports. Check Actions for disabled/queued/cancelled runs; enable the workflow and use **Run workflow** to recover. Extremely delayed runs outside the windows are explicitly skipped in logs.

## Least-privilege publication

One `Publish PULSE` workflow handles push/main, schedule and manual dispatch. `pulse-production` concurrency with cancellation prevents overlapping production runs. Collection checks out current main without persisted credentials, has **contents:read only**, runs bounded fetching, validates, tests, builds with `/${repository.name}/` (trailing period included) and uploads that exact `dist` Pages artifact plus a separate state artifact.

A separate persist job alone has **contents:write**. It verifies that current main is still the collected base, copies only `feed.json` and `ingestion-state.json` from the trusted run's artifact and runs `git add -- public/data/feed.json public/data/ingestion-state.json` (never `git add .`). A push conflict fails without force. These are the only generated committed paths. The bot commit is not relied on to trigger any workflow.

The deploy job alone has **pages:write/id-token:write**, plus contents:read for a latest-head guard. It depends explicitly on persist success and publishes the Pages artifact already validated/built by this run. The build is not rerun against a moving branch. A main-head mismatch cancels stale publication. A newer trusted push also cancels an older run through shared concurrency; an already accepted external Pages deployment is ultimately ordered by GitHub's deployment service.

PR validation is in `check.yml`, uses `pull_request` with **contents:read only**, no secrets or persisted checkout credential, no collector, state writes or deployment. There is no `pull_request_target` pathway. Only reviewed main code receives production workflow permissions. GitHub Pages must remain configured for GitHub Actions.

## Private data

Holdings, notes, custom watchlists and backups remain in localStorage and are never read by Actions. News filters for the personal watchlist/portfolio run locally over the same public feed. Matching requires the exact symbol plus a registry-approved name/alias; name-only matches are rejected. Browser requests load only the public static JSON from Pages. No personal query or security list is sent to SEC, GitHub Actions or a backend.

## Operations

Run **Actions → Publish PULSE → Run workflow → main** for a manual end-to-end check. Inspect collect logs (individual source errors), persist and deploy separately; a green deployment can correctly publish a blocked/partial status and is not by itself proof of working SEC coverage. Verify the deployed `/pulse-investment-research./data/feed.json`, its `run.url`, attempts and source statuses as well as the visible site. Tests are offline fixtures; working-source claims must be based on the actual manual run and published payload. No paid API, external hosting, Vercel, Supabase, user token or AI service is used.
