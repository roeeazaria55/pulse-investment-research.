// Schema construction is checked in alongside its generated JSON document.
import { writeFileSync } from "node:fs";
const str = { type: "string" },
  count = { type: "integer", minimum: 0 },
  date = { type: "string", format: "date-time" },
  nullableDate = { anyOf: [date, { type: "null" }] },
  nullableDay = {
    anyOf: [{ type: "string", format: "date" }, { type: "null" }],
  },
  url = { type: "string", format: "uri", pattern: "^https://" },
  nullableUrl = { anyOf: [url, { type: "null" }] };
const obj = (properties, required = Object.keys(properties)) => ({
  type: "object",
  additionalProperties: false,
  required,
  properties,
});
const nullableStr = { anyOf: [str, { type: "null" }] };
const security = obj({
  id: { type: "string", pattern: "^[a-z0-9-]{3,80}$" },
  name: str,
  ticker: nullableStr,
  exchange: nullableStr,
  cik: { anyOf: [{ type: "string", pattern: "^\\d{10}$" }, { type: "null" }] },
  shareClass: nullableStr,
  aliases: { type: "array", items: str },
  acceptedLegalNames: { type: "array", items: str },
  verification: obj({
    status: { enum: ["verified", "unverified"] },
    date: nullableDay,
    source: nullableUrl,
    method: str,
  }),
  source: {
    anyOf: [
      obj({
        id: str,
        kind: { const: "sec-submissions" },
        url,
        policyUrl: url,
        policyReviewedAt: { type: "string", format: "date" },
      }),
      { type: "null" },
    ],
  },
});
const source = obj({
  id: str,
  securityId: str,
  name: str,
  url: nullableUrl,
  status: {
    enum: ["ok", "blocked", "error", "identity-mismatch", "no-source"],
  },
  lastAttemptAt: nullableDate,
  lastSuccessfulAt: nullableDate,
  errorCode: { anyOf: [str, { type: "null" }] },
  newCount: count,
  availableCount: count,
});
const news = obj({
  id: str,
  securityId: str,
  sourceId: str,
  documentId: { type: "string", pattern: "^\\d{10}-\\d{2}-\\d{6}$" },
  sourceName: { const: "SEC EDGAR submissions" },
  ticker: str,
  company: str,
  headline: str,
  originalTitle: str,
  titleOrigin: { enum: ["primaryDocDescription", "form"] },
  sourceUrl: url,
  publishedAt: nullableDate,
  publicationTimeBasis: { enum: ["SEC acceptanceDateTime", "unknown"] },
  filingDate: nullableDay,
  collectedAt: date,
  importance: { enum: ["high", "medium", "low"] },
  classification: obj({ rule: str, reason: str }),
  form: str,
  summary: str,
  summaryKind: { const: "metadata-only" },
  demo: { const: false },
});
const briefing = obj({
  id: str,
  date: { type: "string", format: "date" },
  period: { enum: ["morning", "evening"] },
  timezone: { const: "Asia/Jerusalem" },
  generatedAt: date,
  kind: { const: "rule-template" },
  status: { enum: ["complete", "partial", "failed", "no-coverage"] },
  itemIds: { type: "array", uniqueItems: true, items: str },
  bootstrap: { type: "boolean" },
  noNewItems: { type: "boolean" },
  failedSourceCount: count,
  questions: { type: "array", items: str },
  notice: str,
});
const schema = {
  $schema: "http://json-schema.org/draft-07/schema#",
  title: "PULSE public feed v2",
  ...obj({
    version: { const: 2 },
    demo: { const: false },
    updatedAt: nullableDate,
    lastAttemptAt: date,
    lastSuccessfulAt: nullableDate,
    status: { enum: ["complete", "partial", "failed", "no-coverage"] },
    newCount: count,
    noNewItems: { type: "boolean" },
    coverage: obj({
      total: count,
      verified: count,
      working: count,
      uncovered: count,
    }),
    sources: { type: "array", items: source },
    registry: obj({
      version: { const: 1 },
      reviewedAt: { type: "string", format: "date" },
      scope: str,
      securities: { type: "array", minItems: 1, items: security },
    }),
    news: { type: "array", maxItems: 600, items: news },
    research: { type: "array", maxItems: 0 },
    briefings: { type: "array", maxItems: 28, items: briefing },
    run: obj({ url: nullableUrl, trigger: str }),
    limitations: { type: "array", items: str },
  }),
};
schema.properties.articles = {type:'array',maxItems:600,items:{$ref:'discovery.schema.json#/definitions/article'}};
schema.properties.discovery = {$ref:'discovery.schema.json#/definitions/discovery'};
writeFileSync(
  "schemas/feed-v2.schema.json",
  JSON.stringify(schema, null, 2) + "\n",
);
