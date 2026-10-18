# Official company source pilot

Scope: NBIS (Nebius Group), IREN and DLO (dLocal). The research screen contains
reviewed issuer news/financial portals, source health, retained document links,
and a previewable Hebrew research pack for manual use in ChatGPT. This adds no
paid model, automatic AI summary, notification, or financial metric extraction.

The reviewed registry is `public/data/official-registry.json`. Nebius links are
from its own newsroom and financial library. IREN and dLocal use their public,
issuer-branded GCS investor portals. These are explicit source selections, not
runtime fallback endpoints for bypassing a block. Denied sources are marked as
failed; no browser spoofing or proxies are used.

`scripts/official_sources.py` collects six index pages, at most eight links per
source and at most three HTML detail pages per company. It reuses the bounded
allowlisted IR client. No PDF is downloaded or parsed. No release body is saved.
A link found on an official index is labeled `index-link`; reading a valid release
heading upgrades it to `page-metadata`. This never claims content analysis.
Dates come only from explicit publication metadata, not a report period, event
date, inferred midnight or collection time. An unknown date remains null.
A future-results announcement is distinguished from actual results in card labels.

IDs use company identity plus the canonical document URL, preserving necessary
query parameters. First collection time stays stable; last-seen and last metadata
check times are separate. Failed indexes retain old valid items and their last
success time. Empty/dynamic pages with no supported links are failures requiring
review, not proof of no news. Maximum retained items: 24 per company, 72 total.
These bounds and selected sources do not establish comprehensive coverage.

The independent snapshot is collected, tested, built and persisted by the same
publication workflow as the public news feed. It cannot change personal research,
portfolio data or notification settings. The frontend checks company/source/link
attribution before displaying it. The service worker uses a network-first snapshot
and a retained offline copy; displayed collection dates expose staleness.

The pack includes up to 12 retained links, source availability, date uncertainty,
company-specific questions, and instructions to open sources before analysis.
It includes no personal holdings, balances or notes. It is previewed and copied
only on the user's action; no chat is submitted automatically.

Validation includes simulated provider failures, redirect/URL allowlists in the
shared client, stable IDs, unknown dates, bounded request counts, no PDF fetching,
wrong attribution and links, source status honesty, pack separation, refresh
failure retention, offline metadata and the production snapshot. The mobile CI
check opens the pack at 320/390/430 pixels. Physical phone testing is separate.
