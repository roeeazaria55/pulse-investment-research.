# Thesis monitoring pilot — 20 October 2026

NBIS and SNDK now have six company-specific monitoring disclosures in the research overview. Each records the baseline in the supplied research, the forward assumption (or the absence of a numerical threshold), why it affects value, what to check next and what would require reconsidering the thesis. Source and assumption buttons focus the respective chapter of the full analysis, expanding it if necessary.

The data source remains the supplied PDFs imported in PR16. This change does not independently verify the underlying market facts, add a live quote feed, import a newer report or change either primary valuation. Observations are explicitly identified as the baseline contained in the dated research, rather than the latest available market data. Company guidance is distinguished from research assumptions; incomplete capital/funding bridges remain visible.

## Comparison contract

`metricComparison` only computes a numerical gap when period, unit and accounting definition all match. Missing observations are not zero. Quarterly or half-year results are not compared directly with annual forecasts. Adjusted EPS is not automatically compared with normalized EPS. Qualitative metrics receive no numeric score, and a numerical variance does not automatically mean the thesis passed or failed. No arbitrary alert thresholds were introduced.

Structured metric observations and targets retain their period, unit and definition to support a subsequent reviewed report ingestion step. There is no automatic updating or personal observation entry in this pilot. This is shown in the UI.

## Valuation contract

The overview and valuation tab identify the source document's reference price and date, explicitly marking it as non-live, and distinguish:

- NBIS: 12-month valuation to 20 October 2027 using 2027 revenue; the active document's simplified net debt and share assumptions are disclosed.
- SNDK: normalized FY2028 earnings valuation with no fixed target date. A 12-month bridge has not yet been built. It needs an explicit earnings period, target-date multiple, future shares and a decision on any discounting, avoiding double discounting.

Published values, scenario weights, source PDFs, historical archives and personal research state are unchanged. The all-company comparison is labelled as research values and targets rather than implying every entry is a 12-month target.

## Next implementation stages

1. Review the pilot with real subsequent reports: extract observations with exact periods, definitions and source references; preserve old baselines and review proposed updates before publishing.
2. Expand company-specific monitoring and source coverage to the other nine researched companies, using each company's business drivers rather than copying these metric lists.
3. Complete a separately sourced SNDK 12-month bridge and strengthen NBIS's funding/dilution bridge before changing the published valuations.
4. Add a compact home attention queue for reporting dates, stale research and reviewed deviations. News should link to affected assumptions.
5. Introduce report version comparisons and an auditable sequence from source through observations, revised assumptions and published valuation. The scheduled metadata collector alone does not constitute automated report analysis.

## Verification

Frontend tests cover mismatched periods/units/definitions, missing/zero values, exact numeric comparisons, source chapter navigation, closed monitoring disclosures and valuation horizon semantics. The mobile regression also opens all twelve metrics at 320/390/430 CSS pixels and at 200% text size. Original research and portfolio/import flows remain in the regression suite.
