/* Bump this identifier when publishing a new application shell. */
const VERSION = "pulse-v7-financial-depth-20261027";
const SCOPE = new URL(self.registration.scope);
const CACHE = `${VERSION}-${SCOPE.pathname}`;
const local = (path) => new URL(path, SCOPE).href;
self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      const response = await fetch(local("./"), { cache: "reload" });
      if (!response.ok) throw Error("Shell unavailable");
      const html = await response.clone().text();
      const assets = [
        ...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g),
      ].map((m) => new URL(m[1], SCOPE).href);
      await cache.put(local("./"), response);
      await cache.addAll([
        ...assets,
        local("manifest.webmanifest"),
        local("icons/icon-192.png"),
        local("icons/icon-512.png"),
        local("icons/maskable-512.png"),
        local("data/feed.json"),
        local("data/official-sources.json"),
      ]);
      // Research is optional during installation; a missing feed must not
      // prevent the application shell from installing.
      for (const path of ["data/latest-research-updates.json", "data/research-update-history.json"]) {
        try {
          const url = local(path);
          const result = await fetch(url, { cache: "no-store" });
          if (result.ok) {
            const body = await result.clone().json();
            if (body.version === 1 && Array.isArray(path.includes("history") ? body.entries : body.reports))
              await cache.put(url, result);
          }
        } catch {/* Remain installable with an honest unavailable state. */}
      }
      await self.skipWaiting();
    })(),
  );
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      for (const key of await caches.keys()) {
        if (
          key.startsWith("pulse-") &&
          key.endsWith(`-${SCOPE.pathname}`) &&
          key !== CACHE
        )
          await caches.delete(key);
      }
      await self.clients.claim();
    })(),
  );
});
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (
    event.request.method !== "GET" ||
    url.origin !== SCOPE.origin ||
    !url.pathname.startsWith(SCOPE.pathname)
  )
    return;
  if (url.pathname.endsWith("/data/feed.json") || url.pathname.endsWith("/data/official-sources.json")) {
    const official = url.pathname.endsWith("/data/official-sources.json");
    const dataKey = local(official ? "data/official-sources.json" : "data/feed.json");
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(event.request);
          if (!response.ok) throw Error("Feed unavailable");
          const body = await response.clone().json();
          if (
            (official ? body.version !== 1 || !Array.isArray(body.items) || !Array.isArray(body.sources) :
            ![1, 2].includes(body.version) || !Array.isArray(body.news) || !Array.isArray(body.research))
          )
            throw Error("Invalid feed");
          const cache = await caches.open(CACHE);
          await cache.put(dataKey, response.clone());
          return response;
        } catch {
          const cached = await caches.match(dataKey);
          return cached || new Response("Unavailable", { status: 503 });
        }
      })(),
    );
    return;
  }
  const researchPath = ["data/latest-research-updates.json", "data/research-update-history.json"]
    .find((path) => url.href === local(path));
  if (researchPath) {
    event.respondWith((async () => {
      const key = local(researchPath);
      try {
        const response = await fetch(event.request);
        if (!response.ok) throw Error("Research feed unavailable");
        const body = await response.clone().json();
        if (body.version !== 1 || !Array.isArray(researchPath.includes("history") ? body.entries : body.reports))
          throw Error("Invalid research feed");
        await (await caches.open(CACHE)).put(key, response.clone());
        return response;
      } catch {
        return (await caches.match(key)) ||
          new Response("Research unavailable", { status: 503 });
      }
    })());
    return;
  }
  if (event.request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(event.request);
          if (!response.ok) throw Error("Unavailable");
          return response;
        } catch {
          return (
            (await caches.match(local("./"))) ||
            new Response("Offline", { status: 503 })
          );
        }
      })(),
    );
    return;
  }
  event.respondWith(
    (async () => {
      const cached = await caches.match(event.request);
      if(cached)return cached;
      const response=await fetch(event.request);
      if(response.ok && /\.(?:js|mjs|css)$/.test(url.pathname)){
        const cache=await caches.open(CACHE);
        await cache.put(event.request,response.clone());
      }
      return response;
    })(),
  );
});
