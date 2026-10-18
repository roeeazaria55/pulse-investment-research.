import { describe, it, expect, vi, afterEach } from "vitest";
import Ajv from "ajv";
import { readFileSync } from "node:fs";
import { parseFeed, isStale } from "../src/data/ingestion";
import { buildPrompt } from "../src/research/prompt";
import { blankResearch, initialState } from "../src/data/initial";
import { readState, validState } from "../src/state/storage";
import schema from "../schemas/feed.schema.json";
const fixture = JSON.parse(
  readFileSync(new URL("../public/data/feed.json", import.meta.url), "utf8"),
);
afterEach(() => vi.unstubAllGlobals());
describe("public data contract", () => {
  it("validates the supplied demo feed against runtime and documented schema", () => {
    expect(parseFeed(fixture).news).toHaveLength(3);
    const ajv = new Ajv({ strict: false });
    ajv.addFormat("date-time", (value) => Number.isFinite(Date.parse(value)));
    ajv.addFormat("uri", (value) => /^https?:\/\//.test(value));
    const validate = ajv.compile(schema);
    expect(validate(fixture), JSON.stringify(validate.errors)).toBe(true);
  });
  it("rejects unsafe URLs, invalid timestamps and falsely live demo data", () => {
    for (const sourceUrl of [
      "javascript:alert(1)",
      "data:text/html,test",
      "not a url",
    ])
      expect(() =>
        parseFeed({ ...fixture, news: [{ ...fixture.news[0], sourceUrl }] }),
      ).toThrow();
    expect(() =>
      parseFeed({
        ...fixture,
        news: [{ ...fixture.news[0], publishedAt: "bad" }],
      }),
    ).toThrow();
    expect(() =>
      parseFeed({
        ...fixture,
        demo: false,
        updatedAt: new Date().toISOString(),
      }),
    ).toThrow();
  });
  it("marks missing, demo and older than 18h information as stale", () => {
    expect(isStale(null)).toBe(true);
    expect(isStale(fixture)).toBe(true);
    const live = {
      ...fixture,
      demo: false,
      news: [],
      updatedAt: "2026-01-01T00:00:00Z",
    };
    expect(isStale(live, Date.parse("2026-01-01T17:00Z"))).toBe(false);
    expect(isStale(live, Date.parse("2026-01-01T19:00Z"))).toBe(true);
  });
});
describe("personal state", () => {
  it("starts without holdings and with exactly eleven unverified watchlist securities", () => {
    const s = initialState();
    expect(s.holdings).toEqual([]);
    expect(s.watchlist).toHaveLength(11);
    expect(s.watchlist.every((w) => !w.verified)).toBe(true);
    expect(validState(s)).toBe(true);
  });
  it("rejects corrupt holdings, invalid research and over-allocation", () => {
    const s = initialState();
    const h = {
      id: "a",
      ticker: "TEST",
      name: "Test",
      allocation: 101,
      averagePrice: 1,
      currency: "USD",
      thesis: "",
      risks: "",
    };
    expect(validState({ ...s, holdings: [h] })).toBe(false);
    expect(validState({ ...s, research: { TEST: { notes: [] } } })).toBe(false);
    expect(
      validState({
        ...s,
        holdings: [
          { ...h, allocation: 60 },
          { ...h, id: "b", allocation: 60 },
        ],
      }),
    ).toBe(false);
  });
  it("does not overwrite corrupt storage", () => {
    const setItem = vi.fn();
    vi.stubGlobal("localStorage", { getItem: () => "{broken", setItem });
    const result = readState();
    expect(result.error).toBeTruthy();
    expect(setItem).not.toHaveBeenCalled();
  });
  it("preserves a valid private portfolio on reload", () => {
    const s = initialState();
    s.research.TEST = { ...blankResearch(), thesis: "Private thesis" };
    vi.stubGlobal("localStorage", { getItem: () => JSON.stringify(s) });
    expect(readState().state).toEqual(s);
  });
});
describe("Hebrew research prompt", () => {
  it("includes the thesis, history, provenance and explicit demonstration labels", () => {
    const r = {
      ...blankResearch(),
      thesis: "Test thesis",
      notes: [
        { id: "1", createdAt: "2026-01-01T00:00:00Z", text: "Earlier note" },
      ],
    };
    const prompt = buildPrompt(
      "Nebius",
      "NBIS",
      r,
      [fixture.news[0]],
      ["https://example.com/filing"],
    );
    expect(prompt).toContain("Test thesis");
    expect(prompt).toContain("Earlier note");
    expect(prompt).toContain("[הדגמה בלבד]");
    expect(prompt).toContain(fixture.news[0].sourceUrl);
    expect(prompt).toContain("https://example.com/filing");
    expect(prompt).toContain("אל תמציא נתונים");
  });
});
