import Ajv from "ajv";
import schema from "../../schemas/feed-v2.schema.json";
import discoverySchema from "../../schemas/discovery.schema.json";
import { validateDiscovery } from "./discoveryValidation.mjs";
import intelligenceSchema from '../../schemas/intelligence.schema.json';
import { validateIntelligence } from './intelligenceValidation.mjs';
import type { LiveFeed, Security } from "../types";
const ajv = new Ajv({ strict: false });
ajv.addFormat(
  "date-time",
  (v) =>
    /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(v) &&
    Number.isFinite(Date.parse(v)),
);
ajv.addFormat(
  "date",
  (v) => /^\d{4}-\d{2}-\d{2}$/.test(v) && Number.isFinite(Date.parse(v)),
);
ajv.addFormat("uri", (v) => {
  try {
    return new URL(v).protocol === "https:";
  } catch {
    return false;
  }
});
ajv.addSchema(discoverySchema);
ajv.addSchema(intelligenceSchema);
const validate = ajv.compile(schema);
export function parseV2(x: unknown): LiveFeed {
  if (!validate(x)) throw Error("פיד ציבורי פגום");
  const f = x as unknown as LiveFeed;
  validateDiscovery(f);
  validateIntelligence(f);
  const ids = new Set<string>();
  if (
    new Set(f.registry.securities.map((s) => s.id)).size !==
      f.registry.securities.length ||
    f.sources.length !== f.registry.securities.length ||
    new Set(f.sources.map((s) => s.securityId)).size !== f.sources.length
  )
    throw Error("רישום מקורות פגום");
  for (const s of f.registry.securities) {
    if (
      typeof s.id !== "string" ||
      typeof s.name !== "string" ||
      !Array.isArray(s.aliases) ||
      !["verified", "unverified"].includes(s.verification?.status)
    )
      throw Error("זהות מקור חסרה");
    if (
      s.verification.status === "verified" &&
      (!s.ticker ||
        !s.exchange ||
        !s.shareClass ||
        !/^\d{10}$/.test(s.cik || "") ||
        !s.verification.date ||
        !s.verification.source?.startsWith("https://www.sec.gov/Archives/") ||
        s.source?.url !== `https://data.sec.gov/submissions/CIK${s.cik}.json`)
    )
      throw Error("זהות מקור לא מאומתת");
  }
  for (const n of f.news) {
    const s = f.registry.securities.find((s) => s.id === n.securityId);
    if (
      !s ||
      s.verification.status !== "verified" ||
      n.sourceId !== s.source?.id ||
      n.ticker !== s.ticker ||
      n.company !== s.name ||
      n.id !== `sec:${s.cik}:${n.documentId}` ||
      ids.has(n.id) ||
      !n.sourceUrl.startsWith(
        `https://www.sec.gov/Archives/edgar/data/${Number(s.cik)}/${n.documentId?.replaceAll("-", "")}/`,
      )
    )
      throw Error("שיוך דיווח לא תקין");
    ids.add(n.id);
  }
  for (const s of f.sources) {
    const r = f.registry.securities.find((r) => r.id === s.securityId);
    if (
      !r ||
      s.id !== (r.source?.id || `none-${r.id}`) ||
      s.url !== (r.source?.url || null)
    )
      throw Error("שיוך מקור לא תקין");
  }
  if (f.status !== "complete" && f.lastSuccessfulAt === f.lastAttemptAt)
    throw Error("חותמת הצלחה מטעה");
  if (f.status === "complete" && f.sources.some((s) => s.status !== "ok"))
    throw Error("הצלחה מלאה מטעה");
  if (
    f.coverage.total !== f.registry.securities.length ||
    f.coverage.working !== f.sources.filter((s) => s.status === "ok").length
  )
    throw Error("ספירת כיסוי לא תקינה");
  return f.articles ? { ...f, news: [...f.news, ...f.articles].map(n=>({...n,rating:f.intelligence?.ratings[n.id]})).sort((a,b) => (b.publishedAt || b.collectedAt).localeCompare(a.publishedAt || a.collectedAt)) } : f;
}
const norm = (x: string) =>
  x.toLowerCase().replace(/[^a-z0-9\u0590-\u05ff]/g, "");
// Personal entries are never uploaded and never promoted to verified identities.
// Match an explicit symbol AND an approved name/alias; similar names alone fail.
export function resolveSecurity(
  feed: LiveFeed,
  personal: Pick<Security, "ticker" | "name">,
) {
  return feed.registry.securities.find(
    (s) =>
      ((s.verification.status === "verified" && s.ticker === personal.ticker) || feed.discovery?.registry.companies.some(c => c.id === s.id && [c.name,...c.aliases].some(n => norm(n) === norm(personal.name)))) &&
      [s.name, ...s.aliases, ...s.acceptedLegalNames, ...(feed.discovery?.registry.companies.find(c => c.id === s.id)?.aliases || [])].some(
        (n) => norm(n) === norm(personal.name),
      ),
  );
}
