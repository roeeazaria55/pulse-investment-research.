# New research supplied as source PDFs — 20 October 2026

The two five-page PDFs supplied by the user replace the reconstructed NBIS/SNDK research as the active reading and valuation. All 12 NBIS and 13 Sandisk numbered sections are represented as structured paragraphs and tables. Source PDFs are copied unchanged into `public/research/`, linked from the reading/valuation, and identified by SHA-256. Their original Library files are not edited.

NBIS: EV/sales on 2027 revenue (5,500/8,500/12,000 million), multiples 4/6/8, net debt 4,000 million and 300 million shares. Bear/Base/Bull weights are explicitly named 20/50/30, avoiding RTL ambiguity. Unrounded values 60/156.6667/306.6667 produce weighted 182.3333, matching the source's approximate 182.3; recomputing rounded 60/157/307 would incorrectly produce 182.6. The reference price is the document's 170.24, not a live quote. The discounted 2030 check around 207 remains separate, with its 15%/four-year assumptions and warning that it is not a full DCF.

Sandisk: normalized FY2028 EPS 65/145/220 times 8/11/13 gives 520/1,595/2,860; 20/50/30 gives 1,759.50. This is explicitly FY2028-based valuation, not a fixed twelve-month target. The reference is the document's 1,371.12. The approximate DCF around 1,150, its limitations and the updated NBM stress cases 1,320/855/520 are retained independently. The severe 520 stress is not presented as the automatic outcome of any NAND-price decline; stress-case probabilities are not invented.

The source assumptions, forecasts, factual claims and caveats are imported as supplied research, not represented as a new independent market-data verification. The source's horizon, unit, fiscal/calendar, GAAP/non-GAAP, prepayment, debt/dilution and Flash Ventures distinctions are preserved. No single average is constructed across methodologies or horizons.

Previous reconstructed baseline JSON is preserved under `src/data/archive/`. Prior quantitative calculators and original historical targets remain inside an explicitly closed archive disclosure; they no longer determine the overview, company comparison or active valuation. Other company models, personal research/imports and macro/earnings features retain their behavior.

Validation includes source-file hashes, all source paragraphs/tables/sections, explicit horizon distinctions, unrounded weighted arithmetic, stress cases, active-versus-archive UI, keyboard chapter navigation, and mobile/200% text with internally scrollable tables. Source PDFs are also verified against their published copies after deployment.
