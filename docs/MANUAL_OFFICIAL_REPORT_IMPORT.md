# PULSE — Controlled official PDF import (fallback only)

**Use only if the existing CI collector cannot retrieve a genuine financial statement.**
GitHub Actions in this **public** repository is not a confidential research delivery
channel. This workflow does **not** download any report, bypass HTTP 403,
invoke paid AI, mutate valuations, or merge the integration PR.

## Exact issuer documents to download from the publishers

1. **FTAI Q2 2026** — official [issuer PDF](https://ftandi.gcs-web.com/node/13051/pdf), [issuer HTML](https://ftandi.gcs-web.com/news-releases/news-release-details/ftai-aviation-ltd-reports-second-quarter-2026-results-increases), or [SEC 10-Q](https://www.sec.gov/Archives/edgar/data/1590364/000162828026051412/ftai-20260630.htm). CIK `1590364`. Make sure it is FTAI **Aviation Ltd.**, not an older FTAI Infrastructure filing.
2. **Enlight Q2 2026** — [official investor Q2 2026 earnings release with full Appendix 1 IFRS statements](https://enlightenergy.com/wp-content/uploads/2026/08/2Q26-Earnings-Release-Eng.pdf); [issuer financial library](https://enlightenergy.com/data/financial-reports/). A prepared-remarks PDF does **not** qualify.
3. **Gilat Telecom Global Q2 2026** — [issuer original 64-page PDF](https://satcom-gilat.co.il/wp-content/uploads/2026/08/%D7%93%D7%95%D7%97-%D7%A8%D7%91%D7%A2%D7%95%D7%9F-2%D7%97%D7%A6%D7%99-%D7%A9%D7%A0%D7%AA%D7%99.pdf); [official financial reports page](https://satcom-gilat.co.il/%D7%93%D7%95%D7%97%D7%95%D7%AA-%D7%9B%D7%A1%D7%A4%D7%99%D7%99%D7%9D/). Issuer: **גילת טלקום גלובל בע"מ**, Israeli corporation number **520041674**, not Gilat Satellite Networks. There was a **corrected** August 20 2026 filing (MAYA reference **2026-01-078165** superseding **2026-01-078119**). Verify the report is the complete/corrected version.

The links point to public official sources and are **not** proof that GitHub Actions
successfully retrieved their bytes. The actual downloaded PDF's SHA-256 is
computed only after the file is supplied and examined.

## Local staging

Use Python 3 with `pdfplumber` from `scripts/requirements-report-intake.txt`.
Download the PDF yourself from an official publisher link. On your trusted
machine create a **private staging directory outside the repository**. Example:

```bash
python3 -m pip install -r scripts/requirements-report-intake.txt
mkdir -p "$HOME/pulse-private-issuer-review"
python3 scripts/manual_official_import.py \
  --issuer candidate-ftai \
  --source-url https://ftandi.gcs-web.com/node/13051/pdf \
  --original-pdf "$HOME/Downloads/ftai-Q2-2026.pdf" \
  --report-period "Q2 2026" --published-date 2026-07-29 \
  --private-staging "$HOME/pulse-private-issuer-review"
```

Use `candidate-enlight` and `candidate-gilat-telecom` for the other issuers,
and their **exact** source URL. For Gilat, omit `--published-date` until the
filing date has been independently corroborated for that PDF version.

The tool performs official allowlist checks, reads real PDF bytes (non-OCR),
verifies issuer identity, extracts original structured tables/statement page
evidence and computes the **SHA-256 of the original PDF bytes**. It creates
three private **owner-only** files with exclusive/non-overwriting writes:

- Original PDF copy.
- One proposed, full `report-intake.json` with retained prior issuer reports.
- Original-byte provenance JSON with hash, period and `pending-review` state.

The files are **not** publicly published and this is **not automatic remote
ingestion**. Never label this private import as a successful GitHub HTTP fetch.
If OCR would be needed, the importer rejects unreadable PDFs. Use source
verification on another official report, not guessed numbers.

## Human review and controlled integration

Before committing anything, a reviewer must verify the PDF SHA against their
copy, issuer legal identity, quarterly versus six-month columns, units, table
page/row, source permissions and the exact source link. Regenerate
`issuer-coverage.json` and `latest-research-updates.json` locally using the
existing scripts after the reviewed `report-intake.json` is deliberately
incorporated into the integration branch. **Do not upload the private source
original to a public repository without a separate licensing decision.**

The automation already preserves previous `report-intake.json` records
across failed HTTP fetches. The full integration branch's real tests and
**new PR head CI** must pass before the owner approves merging.

Do not claim the strict **12/12** release criterion until all twelve have at
least one actually retained source document / original structured filing with
a correctly typed financial observation and auditable provenance.
