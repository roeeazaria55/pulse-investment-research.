import { describe, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import {
  collect,
  parseSubmissions,
  briefingSlot,
  classify,
} from "../scripts/ingest/engine.mjs";
import {
  SourceError,
  createClient,
  approvedTarget,
} from "../scripts/ingest/network.mjs";
import { validateFeed, validateRegistry } from "../scripts/ingest/validate.mjs";
const registry = JSON.parse(
  readFileSync(
    new URL("../public/data/registry.json", import.meta.url),
    "utf8",
  ),
);
export const smallRegistry = {
  ...registry,
  securities: registry.securities.filter((s) => s.source),
};
const stamp = "2026-10-18T04:23:00Z";
export function submissions(s = registry.securities[0], overrides = {}) {
  return {
    cik: Number(s.cik),
    name: s.name,
    tickers: [s.ticker],
    exchanges: [s.exchange],
    filings: {
      recent: {
        accessionNumber: ["0001234567-26-000001"],
        form: ["10-Q"],
        filingDate: ["2026-10-16"],
        acceptanceDateTime: ["2026-10-16T15:05:00Z"],
        primaryDocument: ["report.htm"],
        primaryDocDescription: ["ORIGINAL 10-Q TITLE"],
      },
    },
    ...overrides,
  };
}
const getter = async (url) =>
  submissions(registry.securities.find((s) => s.source?.url === url));
describe("verified public collection", () => {
  it("keeps eight provisional companies uncovered and validates provenance", async () => {
    expect(validateRegistry(registry)).toBe(true);
    const { feed } = await collect({ registry, getJson: getter, now: stamp });
    expect(feed.coverage).toEqual({
      total: 11,
      verified: 3,
      working: 3,
      uncovered: 8,
    });
    expect(feed.status).toBe("partial");
    expect(feed.lastSuccessfulAt).toBeNull();
    expect(feed.news).toHaveLength(3);
    expect(validateFeed(feed)).toBe(true);
    expect(feed.news[0].headline).toBe("ORIGINAL 10-Q TITLE");
  });
  it("deduplicates stable CIK/accession IDs within and across runs and periods", async () => {
    const duplicate = async (url) => {
      const d = await getter(url);
      for (const k of Object.keys(d.filings.recent))
        d.filings.recent[k].push(d.filings.recent[k][0]);
      return d;
    };
    const first = await collect({ registry, getJson: duplicate, now: stamp });
    expect(first.feed.news).toHaveLength(3);
    expect(first.feed.newCount).toBe(3);
    const second = await collect({
      registry,
      previous: first.feed,
      state: first.state,
      getJson: getter,
      now: "2026-10-18T16:23:00Z",
    });
    expect(second.feed.news).toHaveLength(3);
    expect(second.feed.newCount).toBe(0);
    expect(second.feed.noNewItems).toBe(true);
    expect(second.feed.briefings[0].itemIds).toHaveLength(0);
    expect(second.feed.news[0].collectedAt).toBe(stamp);
  });
  it("rejects wrong CIK, issuer, ticker, exchange and reordered dual listing mismatch", () => {
    const s = registry.securities[0];
    for (const override of [
      { cik: 1691421 },
      { name: "Meta Materials Inc." },
      { tickers: ["MMAT"] },
      { exchanges: ["NYSE"] },
      { tickers: ["META", "OTHER"], exchanges: ["NYSE", "Nasdaq"] },
    ])
      expect(() =>
        parseSubmissions(s, submissions(s, override), stamp),
      ).toThrow("identity-mismatch");
  });
  it("keeps missing publication time null, retains filing date, never invents midnight", () => {
    const d = submissions();
    delete d.filings.recent.acceptanceDateTime;
    const [n] = parseSubmissions(registry.securities[0], d, stamp);
    expect(n.publishedAt).toBeNull();
    expect(n.filingDate).toBe("2026-10-16");
    expect(n.publicationTimeBasis).toBe("unknown");
  });
  it("preserves old valid news and prior success when one source fails", async () => {
    const a = await collect({
      registry: smallRegistry,
      getJson: getter,
      now: stamp,
    });
    expect(a.feed.status).toBe("complete");
    const b = await collect({
      registry: smallRegistry,
      previous: a.feed,
      state: a.state,
      getJson: async (url) => {
        if (url.includes("1326801")) throw new SourceError("blocked");
        return getter(url);
      },
      now: "2026-10-18T16:23:00Z",
    });
    expect(b.feed.status).toBe("partial");
    expect(b.feed.lastSuccessfulAt).toBe(stamp);
    expect(b.feed.sources[0].status).toBe("blocked");
    expect(b.feed.sources[0].lastSuccessfulAt).toBe(stamp);
    expect(b.feed.news).toEqual(a.feed.news);
    expect(validateFeed(b.feed)).toBe(true);
  });
  it("does not claim no-new-items or full success when all sources fail", async () => {
    const { feed } = await collect({
      registry,
      getJson: async () => {
        throw new SourceError("blocked");
      },
      now: stamp,
    });
    expect(feed.status).toBe("failed");
    expect(feed.noNewItems).toBe(false);
    expect(feed.lastSuccessfulAt).toBeNull();
    expect(validateFeed(feed)).toBe(true);
  });
  it("handles malformed source atomically without consuming seen IDs", async () => {
    const d = submissions();
    d.filings.recent.form = [];
    const result = await collect({
      registry: { ...registry, securities: [registry.securities[0]] },
      getJson: async () => d,
      now: stamp,
    });
    expect(result.feed.sources[0].errorCode).toBe("malformed-feed");
    expect(result.state.seen).toEqual([]);
    expect(result.feed.news).toEqual([]);
  });
  it("rejects invalid public feed and incorrect company attribution", async () => {
    const { feed } = await collect({ registry, getJson: getter, now: stamp });
    expect(() =>
      validateFeed({
        ...feed,
        news: [{ ...feed.news[0], company: "Wrong company" }],
      }),
    ).toThrow();
    expect(() => validateFeed({ ...feed, lastSuccessfulAt: stamp })).toThrow();
    expect(() =>
      validateFeed({ ...feed, news: [feed.news[0], feed.news[0]] }),
    ).toThrow();
    expect(() => validateFeed({ ...feed, version: 9 })).toThrow();
  });
  it("uses Jerusalem calendar across winter/summer time and merges one slot without duplicates", async () => {
    expect(briefingSlot("2026-07-01T21:30:00Z").date).toBe("2026-07-02");
    expect(briefingSlot("2026-01-01T21:30:00Z").date).toBe("2026-01-01");
    expect(briefingSlot("2026-03-27T04:23:00Z").period).toBe("morning");
    const a = await collect({ registry, getJson: getter, now: stamp });
    const b = await collect({
      registry,
      previous: a.feed,
      state: a.state,
      getJson: getter,
      now: "2026-10-18T05:23:00Z",
    });
    expect(b.feed.briefings).toHaveLength(1);
    expect(b.feed.briefings[0].itemIds).toHaveLength(3);
  });
  it("explains importance through form rules, never content sentiment", () => {
    expect(classify("10-Q").rule).toBe("periodic-report-v1");
    expect(classify("6-K").importance).toBe("medium");
    expect(classify("4").importance).toBe("low");
  });
});
describe("bounded network client", () => {
  it("does not retry blocked sources or switch endpoints", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response("", { status: 403 }));
    const get = createClient({
      fetchImpl,
      sleep: async () => {},
      intervalMs: 0,
    });
    await expect(get(registry.securities[0].source.url)).rejects.toThrow(
      "blocked",
    );
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
  it("bounds retries and uses exponential backoff for transient errors", async () => {
    const sleep = vi.fn().mockResolvedValue();
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response("", { status: 503 }));
    await expect(
      createClient({ fetchImpl, sleep, intervalMs: 0 })(
        registry.securities[0].source.url,
      ),
    ).rejects.toThrow("temporary-http");
    expect(fetchImpl).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledWith(1000);
    expect(sleep).toHaveBeenCalledWith(2000);
  });
  it("rejects credentials, IPs, non-HTTPS, ports and unapproved redirects", async () => {
    for (const url of [
      "http://data.sec.gov/submissions/CIK0001326801.json",
      "https://127.0.0.1/submissions/CIK0001326801.json",
      "https://data.sec.gov:444/submissions/CIK0001326801.json",
      "https://user:pass@data.sec.gov/submissions/CIK0001326801.json",
    ])
      expect(() => approvedTarget(url)).toThrow("unsafe-target");
    const fetchImpl = vi.fn().mockResolvedValue(
      new Response("", {
        status: 302,
        headers: { location: "https://evil.example/a.json" },
      }),
    );
    await expect(
      createClient({ fetchImpl, sleep: async () => {} })(
        registry.securities[0].source.url,
      ),
    ).rejects.toThrow("unsafe-target");
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
  it("bounds response sizes even without content length and rejects HTML/invalid JSON", async () => {
    const url = registry.securities[0].source.url;
    for (const [response, code] of [
      [
        new Response("123456", {
          headers: { "content-type": "application/json" },
        }),
        "size-limit",
      ],
      [new Response("<html>"), "invalid-content-type"],
      [
        new Response("{broken", {
          headers: { "content-type": "application/json" },
        }),
        "invalid-json",
      ],
    ]) {
      await expect(
        createClient({
          fetchImpl: async () => response,
          sleep: async () => {},
          maxBytes: code === "size-limit" ? 5 : 100,
        })(url),
      ).rejects.toThrow(code);
    }
  });
});
