import { readFile, writeFile, rename, appendFile } from "node:fs/promises";
import { createClient } from "./network.mjs";
import { collect, briefingSlot } from "./engine.mjs";
import { validateFeed, validateRegistry } from "./validate.mjs";
const load = async (path) => JSON.parse(await readFile(path, "utf8"));
const registry = await load("public/data/registry.json");
validateRegistry(registry);
const previous = await load("public/data/feed.json");
// Never overwrite a corrupt persisted v2 feed with an empty replacement.
if (previous.version === 2) validateFeed(previous);
else if (previous.version !== 1 || previous.demo !== true)
  throw Error("Unsupported prior feed");
let state;
try {
  state = await load("public/data/ingestion-state.json");
} catch (e) {
  if (e.code === "ENOENT" && previous.version === 1)
    state = { version: 1, seen: [], briefings: [], completedSlots: [] };
  else throw e;
}
if (
  state.version !== 1 ||
  !Array.isArray(state.seen) ||
  !state.seen.every((x) => typeof x === "string") ||
  new Set(state.seen).size !== state.seen.length ||
  state.seen.length > 100000 ||
  !Array.isArray(state.completedSlots || [])
)
  throw Error("Invalid processing state; preserving previous files");
if (
  previous.version === 2 &&
  previous.news.some((n) => !state.seen.includes(n.id))
)
  throw Error(
    "Processing state lost IDs for retained news; manual recovery required",
  );
const now = new Date().toISOString();
const trigger = process.env.GITHUB_EVENT_NAME || "local";
const slot = briefingSlot(now);
const slotId = `${slot.date}:${slot.period}`;
// Phase 3 polls throughout the day. Daily publication deduplication is handled
// independently by the fixed Jerusalem 13:00 window in build_intelligence.py.
const result = await collect({
  registry,
  previous,
  state,
  getJson: createClient({ userAgent: process.env.SEC_USER_AGENT || undefined }),
  now,
  trigger,
  runUrl: process.env.GITHUB_RUN_ID
    ? `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
    : null,
});
const eligible = result.feed.sources.filter((s) => s.url);
// Optional news discovery runs independently of SEC. Preserve the complete prior
// extension if the collector itself could not produce a valid replacement.
try {
  const discovery = await load('work/discovery.json');
  if (discovery.discovery.lastAttemptAt < previous.discovery?.lastAttemptAt) throw Error('Old discovery result');
  result.feed.articles = discovery.articles;
  result.feed.discovery = discovery.discovery;
} catch (e) {
  if (e.code !== 'ENOENT') throw e;
  if (previous.discovery) throw Error('Expected fresh discovery output; refusing a misleading publication');
}
result.state.completedSlots = [
  ...new Set([
    ...(state.completedSlots || []),
    ...((result.feed.discovery ? result.feed.discovery.status === 'complete' : eligible.length && eligible.every((s) => s.status === "ok"))
      ? [slotId]
      : []),
  ]),
].slice(-60);
validateFeed(result.feed);
// Fixed paths only. No fetched strings become commands or filesystem targets.
for (const [path, data] of [
  ["public/data/feed.json", result.feed],
  ["public/data/ingestion-state.json", result.state],
]) {
  await writeFile(`${path}.tmp`, JSON.stringify(data, null, 2) + "\n");
  await rename(`${path}.tmp`, path);
}
if (process.env.GITHUB_OUTPUT)
  await appendFile(process.env.GITHUB_OUTPUT, "skipped=false\n");
if (process.env.GITHUB_STEP_SUMMARY && result.feed.discovery) {
  const d=result.feed.discovery;
  await appendFile(process.env.GITHUB_STEP_SUMMARY,
    `## Public headline discovery\n\nStatus: **${d.status}**. Retained headlines: **${result.feed.articles.length}**. Newly discovered: ${d.newCount}.\n\n| Company | Provider | Search result | Count |\n| --- | --- | --- | --- |\n${d.sources.map(s=>`| ${s.securityId} | ${s.provider} | ${s.status} | ${s.count} |`).join('\n')}\n\nGDELT remains disabled after HTTP 429 in the feasibility run. SEC status below is supplemental and independent.\n`);
}
if (process.env.GITHUB_STEP_SUMMARY)
  await appendFile(
    process.env.GITHUB_STEP_SUMMARY,
    `## Public source health\n\nCollection status: **${result.feed.status}**. Working sources: **${result.feed.coverage.working}/${result.feed.coverage.total}**. New records: ${result.feed.newCount}.\n\nA successful workflow can publish an honest failed/partial collection status; it is not proof of active coverage.\n\n| Source | Status | Error |\n| --- | --- | --- |\n${result.feed.sources.map((s) => `| ${s.id} | ${s.status} | ${s.errorCode || "—"} |`).join("\n")}\n`,
  );
console.log(
  JSON.stringify({
    status: result.feed.status,
    newCount: result.feed.newCount,
    coverage: result.feed.coverage,
    sources: result.feed.sources.map((s) => ({
      id: s.id,
      status: s.status,
      error: s.errorCode,
    })),
  }),
);
