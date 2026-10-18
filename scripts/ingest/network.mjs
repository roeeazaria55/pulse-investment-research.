// Only the explicitly approved public SEC submissions API is fetched.
// No browser-like spoofing, proxies, alternate hosts or paywall workarounds.
export class SourceError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}
export function approvedTarget(input) {
  let u;
  try {
    u = new URL(input);
  } catch {
    throw new SourceError("unsafe-target");
  }
  if (
    u.protocol !== "https:" ||
    u.hostname !== "data.sec.gov" ||
    u.port ||
    u.username ||
    u.password ||
    u.search ||
    u.hash ||
    !/^\/submissions\/CIK\d{10}\.json$/.test(u.pathname)
  )
    throw new SourceError("unsafe-target");
  return u.href;
}
export function createClient({
  fetchImpl = fetch,
  sleep = (ms) => new Promise((r) => setTimeout(r, ms)),
  now = Date.now,
  userAgent = "PULSE/2.0 public research (administrative contact: https://github.com/roeeazaria55/pulse-investment-research./issues)",
  maxBytes = 2 * 1024 * 1024,
  timeoutMs = 15000,
  intervalMs = 1100,
} = {}) {
  let nextAt = 0;
  return async function getJson(input) {
    approvedTarget(input);
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        let url = input;
        for (let hop = 0; hop <= 2; hop++) {
          url = approvedTarget(url);
          await sleep(Math.max(0, nextAt - now()));
          nextAt = now() + intervalMs;
          const response = await fetchImpl(url, {
            redirect: "manual",
            headers: { "User-Agent": userAgent, Accept: "application/json" },
            signal: AbortSignal.timeout(timeoutMs),
          });
          if ([301, 302, 303, 307, 308].includes(response.status)) {
            await response.body?.cancel();
            const destination = response.headers.get("location");
            if (!destination || hop === 2)
              throw new SourceError("redirect-limit");
            url = approvedTarget(new URL(destination, url).href);
            continue;
          }
          if ([401, 403, 451].includes(response.status)) {
            await response.body?.cancel();
            throw new SourceError("blocked");
          }
          if (response.status === 429 || response.status >= 500) {
            await response.body?.cancel();
            throw new SourceError("temporary-http");
          }
          if (!response.ok) {
            await response.body?.cancel();
            throw new SourceError("http-error");
          }
          if (
            !/application\/json/i.test(
              response.headers.get("content-type") || "",
            )
          ) {
            await response.body?.cancel();
            throw new SourceError("invalid-content-type");
          }
          if (Number(response.headers.get("content-length") || 0) > maxBytes) {
            await response.body?.cancel();
            throw new SourceError("size-limit");
          }
          const reader = response.body?.getReader();
          if (!reader) throw new SourceError("empty-body");
          let size = 0;
          const chunks = [];
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              size += value.byteLength;
              if (size > maxBytes) throw new SourceError("size-limit");
              chunks.push(value);
            }
          } finally {
            await reader.cancel().catch(() => {});
          }
          try {
            return JSON.parse(Buffer.concat(chunks).toString("utf8"));
          } catch {
            throw new SourceError("invalid-json");
          }
        }
      } catch (error) {
        const code =
          error instanceof SourceError ? error.code : "network-or-timeout";
        if (
          !["temporary-http", "network-or-timeout"].includes(code) ||
          attempt === 2
        )
          throw new SourceError(code);
        await sleep(1000 * 2 ** attempt);
      }
    }
    throw new SourceError("network-or-timeout");
  };
}
