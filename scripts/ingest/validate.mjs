import Ajv from "ajv";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { approvedTarget } from "./network.mjs";
import { validateDiscovery } from "../../src/data/discoveryValidation.mjs";
import { validateIntelligence } from "../../src/data/intelligenceValidation.mjs";
const schema = JSON.parse(
  readFileSync(
    new URL("../../schemas/feed-v2.schema.json", import.meta.url),
    "utf8",
  ),
);
const ajv = new Ajv({ allErrors: true, strict: false });
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
ajv.addSchema(JSON.parse(readFileSync(new URL('../../schemas/discovery.schema.json', import.meta.url),'utf8')));
ajv.addSchema(JSON.parse(readFileSync(new URL('../../schemas/intelligence.schema.json', import.meta.url),'utf8')));
const validate = ajv.compile(schema);
export function validateRegistry(registry) {
  if (
    registry?.version !== 1 ||
    !Array.isArray(registry.securities) ||
    !registry.securities.length
  )
    throw Error("Invalid registry");
  const ids = new Set(),
    listings = new Set(),
    sources = new Set();
  for (const s of registry.securities) {
    if (
      typeof s.id !== "string" ||
      !/^[a-z0-9-]{3,80}$/.test(s.id) ||
      ids.has(s.id) ||
      typeof s.name !== "string" ||
      !Array.isArray(s.aliases) ||
      !s.aliases.every((a) => typeof a === "string") ||
      !Array.isArray(s.acceptedLegalNames) ||
      !["verified", "unverified"].includes(s.verification?.status)
    )
      throw Error("Invalid registry identity");
    ids.add(s.id);
    if (s.verification.status === "verified") {
      if (
        !s.ticker ||
        !s.exchange ||
        !s.shareClass ||
        !/^\d{10}$/.test(s.cik || "") ||
        !s.acceptedLegalNames.length ||
        !/^\d{4}-\d{2}-\d{2}$/.test(s.verification.date || "") ||
        !s.verification.source?.startsWith(
          "https://www.sec.gov/Archives/edgar/data/",
        ) ||
        s.source?.kind !== "sec-submissions"
      )
        throw Error("Incomplete verification");
      if (
        approvedTarget(s.source.url) !==
          `https://data.sec.gov/submissions/CIK${s.cik}.json` ||
        sources.has(s.cik)
      )
        throw Error("Duplicate issuer/source or CIK mismatch");
      sources.add(s.cik);
      const listing = `${s.exchange}:${s.ticker}`;
      if (listings.has(listing)) throw Error("Duplicate listing");
      listings.add(listing);
    } else if (
      s.source !== null ||
      s.verification.date !== null ||
      s.verification.source !== null
    )
      throw Error("Unverified identity cannot enable ingestion");
  }
  return true;
}
export function validateFeed(feed) {
  if (!validate(feed))
    throw Error(`Invalid feed: ${ajv.errorsText(validate.errors)}`);
  validateRegistry(feed.registry);
  validateDiscovery(feed);
  validateIntelligence(feed);
  const securities = new Map(feed.registry.securities.map((s) => [s.id, s]));
  const ids = new Set();
  if (
    feed.sources.length !== securities.size ||
    new Set(feed.sources.map((s) => s.securityId)).size !== securities.size
  )
    throw Error("Missing/duplicate source statuses");
  for (const source of feed.sources) {
    const security = securities.get(source.securityId);
    if (
      !security ||
      source.id !== (security.source?.id || `none-${security.id}`) ||
      source.url !== (security.source?.url || null)
    )
      throw Error("Source attribution mismatch");
  }
  for (const n of feed.news) {
    const s = securities.get(n.securityId);
    if (
      !s ||
      s.verification.status !== "verified" ||
      n.sourceId !== s.source.id ||
      n.ticker !== s.ticker ||
      n.company !== s.name ||
      n.id !== `sec:${s.cik}:${n.documentId}` ||
      ids.has(n.id)
    )
      throw Error("News identity mismatch/duplicate");
    ids.add(n.id);
    const prefix = `https://www.sec.gov/Archives/edgar/data/${Number(s.cik)}/${n.documentId.replaceAll("-", "")}/`;
    if (!n.sourceUrl.startsWith(prefix)) throw Error("Wrong source URL");
  }
  if (
    feed.status !== "complete" &&
    feed.lastSuccessfulAt === feed.lastAttemptAt
  )
    throw Error("Partial/failed run cannot stamp full success");
  if (feed.status === "complete" && feed.sources.some((s) => s.status !== "ok"))
    throw Error("False full success");
  const working = feed.sources.filter((s) => s.status === "ok").length;
  if (
    feed.coverage.total !== securities.size ||
    feed.coverage.working !== working ||
    feed.coverage.uncovered !== securities.size - working
  )
    throw Error("Coverage mismatch");
  if (feed.noNewItems && (feed.newCount !== 0 || working === 0))
    throw Error("False no-new-items result");
  return true;
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  validateFeed(JSON.parse(readFileSync("public/data/feed.json", "utf8")));
  console.log("Public feed schema and provenance valid");
}
