// @vitest-environment jsdom
import React from "react";
import registry from "../public/data/registry.json";
import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  cleanup,
  fireEvent,
  within,
} from "@testing-library/react";
import App from "../src/App";
import { parseV2, resolveSecurity } from "../src/data/feedV2";
import { isStale } from "../src/data/ingestion";
import { collect } from "../scripts/ingest/engine.mjs";
async function fixture() {
  return (
    await collect({
      registry,
      now: new Date().toISOString(),
      getJson: async (url) => {
        const s = registry.securities.find((s) => s.source?.url === url);
        return {
          cik: Number(s.cik),
          name: s.name,
          tickers: [s.ticker],
          exchanges: [s.exchange],
          filings: {
            recent: {
              accessionNumber: ["0001234567-26-000001"],
              form: ["10-Q"],
              filingDate: [new Date().toISOString().slice(0, 10)],
              primaryDocument: ["test-fixture.htm"],
              primaryDocDescription: ["TEST FIXTURE ONLY"],
            },
          },
        };
      },
    })
  ).feed;
}
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});
describe("v2 public display and privacy", () => {
  it("shows partial coverage and unknown publication time without claiming full success", async () => {
    const feed = await fixture();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => feed }),
    );
    render(React.createElement(App));
    expect(
      await screen.findByRole("heading", { name: "כיסוי חלקי" }),
    ).toBeTruthy();
    expect(screen.getByText(/הצלחה מלאה אחרונה: טרם הושגה/)).toBeTruthy();
    expect(screen.getAllByText(/לא נמסר במקור/)).toHaveLength(3);
    expect(
      screen.getByRole("heading", { name: /תדריך .* — תבנית דיווחים/ }),
    ).toBeTruthy();
  });
  it("matches only verified exact symbols and approved names; keeps local watchlist private", async () => {
    const feed = await fixture();
    expect(
      resolveSecurity(feed, { ticker: "META", name: "Meta Platforms" })?.cik,
    ).toBe("0001326801");
    expect(
      resolveSecurity(feed, { ticker: "META", name: "Meta Materials" }),
    ).toBeUndefined();
    expect(
      resolveSecurity(feed, { ticker: "GILT", name: "Gilat Telecom" }),
    ).toBeUndefined();
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => feed });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("scrollTo", vi.fn());
    render(React.createElement(App));
    await screen.findByRole("heading", { name: "כיסוי חלקי" });
    fireEvent.click(
      within(screen.getByRole("navigation", { name: "ניווט נייד" })).getByRole(
        "button",
        { name: "חדשות" },
      ),
    );
    fireEvent.change(screen.getByLabelText("מקור הפריטים"), {
      target: { value: "portfolio" },
    });
    expect(screen.getByText("לא נמצאו פריטים")).toBeTruthy();
    for (const [url, options] of fetchMock.mock.calls) {
      expect(url).toMatch(/^\/data\/feed.json\?schema=2&t=\d+$/);
      expect(options).toEqual({ cache: "no-store" });
    }
  });
  it("validates v2 and rejects malformed registry/identity/false success", async () => {
    const feed = await fixture();
    expect(parseV2(feed)).toBe(feed);
    expect(isStale(feed)).toBe(false);
    for (const changed of [
      { ...feed, lastSuccessfulAt: feed.lastAttemptAt },
      { ...feed, news: [{ ...feed.news[0], ticker: "WRONG" }] },
      {
        ...feed,
        registry: { ...feed.registry, securities: [{ id: "broken" }] },
      },
    ])
      expect(() => parseV2(changed)).toThrow();
    const old = {
      ...feed,
      sources: feed.sources.map((s) =>
        s.url ? { ...s, lastSuccessfulAt: "2020-01-01T00:00:00Z" } : s,
      ),
    };
    expect(isStale(old)).toBe(true);
  });
});
