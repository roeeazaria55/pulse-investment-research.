# PULSE AI Analyst — evidence-first packet contract

## What PR #31 does

The shared `scripts/ai_research_packets.py` adapter reads the existing PULSE
official issuer registry, collected accounting observations, immutable forecast
archive, comparison blocks, **existing analyst research** and **active model
assumptions**. It produces one deterministic JSON packet each for DLO, NBIS,
IREN and SMCI under `public/data/ai-research-packets/`.

No AI calls, no paid provider, no API keys, no scraping beyond the existing
collector, no PDF OCR and **no target price/model/scenario mutations**.

A real DLO Q2 2026 packet contains the **four actual source-derived numbers**
revenue 399.7, gross profit 127.2, operating cash 140.522 and CAPEX 9.91
(all USD millions). These are *test expectations only*, NOT hardcoded into
the production packet builder. All four remain `needs-reconciliation`, are
marked `modelEligible:false`, and are NOT verified historical forecasts.

### Separate trust domains

- `financialObservations`: collected issuer table cells with original raw
  value/unit, source row, exact quarter and source content SHA-256. Allowed
  issuer HTTPS host and exact period are validated.
- `research`: existing user-supplied analyst narrative, retained verbatim
  by named section and explicitly labeled unverified and untrusted as
  instructions.
- `valuationModel`: existing active quantitative model inputs and Bear/Base/
  Bull probabilities if structurally available; research assumptions, **not**
  approved facts or independently verified target prices.
- `archivedForecasts`: content-addressed history with **first-seen**
  timestamps, not backdated research-author timestamps.
- `forecastComparisons`: only already-blocked comparisons; the packet
  builder never adds numerical surprise estimates.
- `legacyResearchPdf`: pointer and file digest (when present); the generator
  does not infer facts from PDFs.
- `trustPolicy`: explicitly no AI execution, no price-target update and no
  personal investment holdings.

No investment holdings, account identifiers, connectors, non-repository
private data or credentials are serialized.

## Generation and scope

Run `python3 scripts/ai_research_packets.py` from repository root.
For PR CI, the existing collector and mapping are run first, then packets
are produced as read-only test artifacts. In the scheduled Pages pipeline,
approved source code from `main` reads `pulse-data` state, generates
packets, publishes them with the site, and writes back **only** the packet
artifacts plus existing allowlisted public state to `pulse-data`.

Output signatures are deterministic over the actual input content: replaying
the same evidence cannot silently change the packet. New source hashes alter
the content-derived packet fingerprint, while earlier accounting observations
and forecasts remain in their existing historical queues.

## Limitations and security review

- The issuer registry has no independently reviewed normalized industry
  taxonomy, so `industry:null` is honest rather than guessed.
- Not every company has an active `models/<ticker>.json`. Missing quantitative
  models are flagged as gaps; they are not filled with narrative price guesses.
- Text excerpts from analyst research may contain inaccurate or adversarial
  prose. They must be supplied to an eventual model as **data**, in a separate
  untrusted context, never as high-priority instructions.
- Public static GitHub Pages is not an approval server. `main` currently
  has no active protected branch ruleset; no analyst approval is verified.
- The packet contract does not infer confidence scores from unreviewed sources,
  trigger trades, modify portfolio holdings or create AI-generated conclusions.

**Future milestone**: a separately reviewed, server-side AI runner accepting
this contract and emitting a schema-validated review proposal. A human-reviewed
GitHub PR remains required before any real valuation changes.

CI must validate the original four DLO source numbers, source metadata,
real four-company data shape, idempotent hashes and deliberate rejection of
tampered issuer URLs, dates or claimed approvals.

This change remains a draft PR; do not merge without permission.
