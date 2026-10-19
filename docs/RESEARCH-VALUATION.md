# Research completion and NBIS scenario worksheet — 2026-10-19

NBIS worksheet description below records the first release; superseded by the
sourced conditional funding/dilution model in [NBIS-VALUATION.md](NBIS-VALUATION.md).

FTAI: read the 2026-06-30 SEC 10-Q (filed July 31), cash-flow statements
pages 9–10 and debt note 6. Negative H1 operating cash flow is separated
from equipment-sale receipts in investing. CFO less PPE is explicitly not
normalized FCF. Borrowings before issuance costs are distinguished from the
carrying amount; future SPV economics and recurring owner cash remain open.

Gilat Telecom Global (not Gilat Satellite Networks): H1 consolidated PDF
pages 30–31 and 38–39. Separate bond carrying amounts, lease principal and
interest, and restricted cash. Arithmetic: 33.246−7.546−0.282−15.318−1.892−1.246
= 6.962 million ILS; after 1.647 bond principal = 5.315. This is not an
issuer-defined FCF metric. Bond carrying values are not redemption values.
Covenant definitions and subsequent conversions remain open.

NextVision: the issuer Financial Reports page links its Hebrew Q2 PDF
`HEB_clean_isa.pdf` under a May upload directory. Contents identify June 30
and approval August 9; path dates are not report dates. PDF page 18 confirms
H1/Q2/FY2025 revenue and profits; page 24 details customer concentration.
Use this as the controlling period mapping rather than presentation columns.
No claim that the presentation itself was corrected.

NBIS: add a standalone three-scenario EV/revenue worksheet, horizon end-2027.
All numeric seeds are illustrative analyst assumptions, not verified forecasts,
market multiples, a current balance sheet, or price targets. Inputs are USD
millions and shares millions. Show enterprise value, raw equity bridge,
zero-floor terminal price and discounted price. All capital inputs must be at
one horizon. Convertible debt must not remain as debt when its conversion
shares are already included. No automatic conversion or current quote.
Edits are temporary and explicitly labeled; personal research is untouched.
A substantive valuation still needs a verified financing/dilution bridge,
forecast and comparable-multiple rationale, then expansion to other companies.

Validation: 73 JS tests, 61 Python tests, production build, mobile Chromium
checks at 320/390/430 with 200% text, editable worksheet validation/reset and
existing PDF/import/persistence checks. See work/mobile-check.json for run.
Rollback: revert the commit `Add sourced cash/debt research bridges and NBIS
scenario worksheet`; no personal browser data migration is introduced.
