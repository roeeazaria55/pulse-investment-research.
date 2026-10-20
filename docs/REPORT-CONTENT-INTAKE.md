# Official report content intake — first production stage

## What runs automatically

After official metadata collection, `scripts/report_intake.py` reads financial report candidates for NBIS, SNDK, DLO, BWAY and SMCI. It uses the existing scheduled GitHub Actions publication workflow, without an AI service or API secret. HTML bodies and up to 60 PDF pages are read under size/time bounds. Financial tables are extracted as candidate source rows; selected inline XBRL concepts retain exact context start/end dates, unit, scale and issuer identity. If a financial release has no supported data but links to an approved PDF, one attachment can be followed. This is distinct from the user-supplied PULSE research PDFs.

The scheduled run persists `public/data/report-intake.json` alongside existing public ingestion state and publishes it. A compact disclosure in each covered company's overview shows documents read, the successful read date, publication date when known, scope, candidate tables, structured facts and links to the actual read document. A failed refresh retains previous successful content and marks the failure. A source failure does not mean no report was published.

## Bounds and attribution

- Only company-registry HTTPS hosts and document paths, including issuer-specific SEC CIK paths. Redirects and PDF links use the same checks. Encoded path traversal is rejected.
- Maximum 8MB per document, 12-second network timeout, 25-second download deadline, 20-second PDF parsing budget and 60-page limit. Partial scope is explicit.
- Up to eight network reads and approximately 120 seconds per run; one candidate per company so early companies cannot consume every slot. The top four financial candidates rotate, prioritizing unseen URLs. Discovery can still be partial or delayed.
- Clinical results, conference announcements and future reporting schedules are not financial results. Documents that contain no supported table/fact retain an honest read-without-data status.
- SHA-256 identifies the exact bytes that were read. Stable URLs are rechecked; up to three previous hash/timestamp records are retained. Historical full report bytes and historical fact sets are not yet an archive feature.
- Table extraction does not infer fiscal periods, units, GAAP status or column meanings from position. It is explicitly pending review. PDF table order can require visual verification. Only supported non-dimensional inline XBRL facts with matching issuer CIK and explicit context/unit are represented as structured-source facts. They are not automatically equivalent to our analyst metrics.
- Full report prose is not republished. Source rows may be bounded/truncated and are labelled as selected rows. Publication dates are not fabricated from collection dates or filenames.

## Supplied research import

The source analysis PDFs of DLO (4 pages, 10 sections), BWAY (3 pages, 16 sections) and SMCI (5 pages, 14 sections) are preserved byte-for-byte, with all numbered sections represented in reading mode. Source tables are retained independently of calculated valuations.

- DLO source scenario prices 8.64/21.14/36.70 are the active stated scenarios, giving 23.308, displayed 23.31. Rounded EPS/net-income rows cannot be multiplied back to reproduce all source targets. The scenario table’s base gross/net profit differ slightly from the annual forecast and require rounding reconciliation; the quarterly forecast rows do sum to their annual totals. These are disclosed, not silently repaired. The prior reference price 14.73 has no date specified in the supplied document. The document's 00:01 Israel call time is preserved as supplied and flagged for reconciliation with its 18:00 New York time; the existing verified earnings calendar was not overwritten.
- BWAY valuation is USD per Nasdaq ADS, not ILS per TASE share. The source assumes 40M diluted shares/ADS; that remains a sensitivity assumption, not a verified current count. The annual report cited by the user states a 1:1 ADS/ordinary ratio effective 3 March 2026; no ILS conversion or local-price upside was invented. The supplied valuation is based on 2027 earnings and contains no fixed target date.
- SMCI uses exact supplied net income/shares before rounding, giving approximately 50.92 versus the PDF's approximate 50.90. Both are disclosed, with the same assumptions. The 12-month horizon is measured from the research date, and the 19 October reference quote is marked non-live.

## Remaining stages

1. Review and map supported extracted observations to the company's monitoring metric definitions, including accounting reconciliations and fiscal periods. Never compare quarter and full-year values directly.
2. Generate a versioned proposed research update with cited evidence. AI narrative analysis, if added, needs a separately configured service and budget; it is not enabled here.
3. Review revised scenario assumptions and capital/funding bridges before replacing the active model. Automatic content intake does not mean automatic valuation approval.
4. Expand report parsing beyond these five companies after testing their source formats.
