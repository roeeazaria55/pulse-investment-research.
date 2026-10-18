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
const hour = Number(
  new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Jerusalem",
    hour: "2-digit",
    hourCycle: "h23",
  }).format(new Date(now)),
);
// Both winter/summer UTC schedules run. Only a local morning/evening window
// may publish; a persisted successful slot prevents the extra DST invocation.
const scheduled = trigger === "schedule";
const inWindow = (hour >= 7 && hour <= 10) || (hour >= 19 && hour <= 22);
if (scheduled && (!inWindow || (state.completedSlots || []).includes(slotId))) {
  if (process.env.GITHUB_OUTPUT)
    await appendFile(process.env.GITHUB_OUTPUT, "skipped=true\n");
  console.log(
    "Skipped schedule outside local window or already processed slot",
  );
  process.exit(0);
}
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
result.state.completedSlots = [
  ...new Set([
    ...(state.completedSlots || []),
    ...(eligible.length && eligible.every((s) => s.status === "ok")
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
