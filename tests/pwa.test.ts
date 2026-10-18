import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
const worker = readFileSync(
  new URL("../public/sw.js", import.meta.url),
  "utf8",
);
function harness() {
  const scope = "https://example.org/pulse-investment-research./";
  const handlers: Record<string, (e: any) => void> = {};
  const entries = new Map<string, Response>();
  const deleted: string[] = [];
  const requested: string[] = [];
  let offline = false;
  const key = (x: any) => (typeof x === "string" ? x : x.url);
  const cache = {
    put: async (k: any, v: Response) => {
      entries.set(key(k), v);
    },
    addAll: async (urls: string[]) => {
      for (const u of urls) {
        requested.push(u);
        entries.set(u, new Response("asset"));
      }
    },
  };
  const self = {
    registration: { scope },
    addEventListener: (event: string, fn: any) => (handlers[event] = fn),
    skipWaiting: async () => {},
    clients: { claim: async () => {} },
  };
  runInNewContext(worker, {
    self,
    URL,
    Response,
    caches: {
      open: async () => cache,
      match: async (r: any) => entries.get(key(r))?.clone(),
      keys: async () => [
        "pulse-old-/pulse-investment-research./",
        "pulse-old-/other-app/",
      ],
      delete: async (k: string) => deleted.push(k),
    },
    fetch: async (input: any) => {
      if (offline) throw Error("offline");
      return new Response(
        '<html><script src="/pulse-investment-research./assets/app.js"></script><link href="/pulse-investment-research./assets/app.css"></html>',
        { status: 200 },
      );
    },
  });
  const install = async () => {
    let done: Promise<unknown> = Promise.resolve();
    handlers.install({ waitUntil: (p: Promise<unknown>) => (done = p) });
    await done;
  };
  const request = async (path: string, mode = "cors") => {
    let response: Promise<Response> | undefined;
    handlers.fetch({
      request: { url: scope + path, method: "GET", mode },
      respondWith: (p: Promise<Response>) => (response = p),
    });
    return response;
  };
  return {
    scope,
    handlers,
    entries,
    deleted,
    requested,
    install,
    request,
    goOffline: () => (offline = true),
  };
}
describe("PWA contract", () => {
  it("declares installable standalone metadata and real PNG icon dimensions", () => {
    const manifest = JSON.parse(
      readFileSync(
        new URL("../public/manifest.webmanifest", import.meta.url),
        "utf8",
      ),
    );
    expect(manifest.display).toBe("standalone");
    expect(manifest.start_url).toBe("./");
    expect(manifest.scope).toBe("./");
    expect(manifest.dir).toBe("rtl");
    expect(manifest.icons.some((i: any) => i.purpose === "maskable")).toBe(
      true,
    );
    for (const icon of manifest.icons) {
      const png = readFileSync(
        new URL("../public/" + icon.src, import.meta.url),
      );
      expect(png.subarray(1, 4).toString()).toBe("PNG");
      expect(`${png.readUInt32BE(16)}x${png.readUInt32BE(20)}`).toBe(
        icon.sizes,
      );
    }
  });
  it("preloads hashed shell assets and icons under the GitHub repository scope", async () => {
    const h = harness();
    await h.install();
    expect(h.requested).toContain(h.scope + "assets/app.js");
    expect(h.requested).toContain(h.scope + "assets/app.css");
    expect(h.requested).toContain(h.scope + "icons/icon-192.png");
    expect(h.entries.has(h.scope)).toBe(true);
  });
  it("serves the cached application shell and feed without network", async () => {
    const h = harness();
    await h.install();
    h.goOffline();
    const page = await h.request("", "navigate");
    expect(await page?.text()).toContain("app.js");
    const feed = await h.request("data/feed.json");
    expect(feed?.status).toBe(200);
  });
  it("cleans up only obsolete caches belonging to this application scope", async () => {
    const h = harness();
    let done: Promise<unknown> = Promise.resolve();
    h.handlers.activate({ waitUntil: (p: Promise<unknown>) => (done = p) });
    await done;
    expect(h.deleted).toEqual(["pulse-old-/pulse-investment-research./"]);
  });
});
