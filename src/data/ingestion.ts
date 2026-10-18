import type { Feed, News, Research } from "../types";
import { researchFields } from "../types";
export const isUrl = (value: unknown): value is string => {
  try {
    return (
      typeof value === "string" &&
      ["https:", "http:"].includes(new URL(value).protocol)
    );
  } catch {
    return false;
  }
};
const isDate = (x: unknown) =>
  typeof x === "string" && Number.isFinite(Date.parse(x));
export function isResearch(x: unknown): x is Research {
  if (!x || typeof x !== "object") return false;
  const r = x as Research;
  return (
    researchFields.every((k) => typeof r[k] === "string") &&
    Array.isArray(r.notes) &&
    r.notes.every(
      (n) =>
        typeof n.id === "string" &&
        typeof n.text === "string" &&
        isDate(n.createdAt),
    )
  );
}
export function isNews(x: unknown): x is News {
  if (!x || typeof x !== "object") return false;
  const n = x as News;
  return (
    ["id", "ticker", "company", "headline", "summary"].every(
      (k) => typeof (n as unknown as Record<string, unknown>)[k] === "string",
    ) &&
    isUrl(n.sourceUrl) &&
    isDate(n.publishedAt) &&
    isDate(n.collectedAt) &&
    ["high", "medium", "low"].includes(n.importance) &&
    typeof n.demo === "boolean"
  );
}
export function parseFeed(x: unknown): Feed {
  if (!x || typeof x !== "object") throw Error("מבנה נתונים לא תקין");
  const f = x as Feed;
  if (
    f.version !== 1 ||
    typeof f.demo !== "boolean" ||
    !(f.updatedAt === null || isDate(f.updatedAt)) ||
    !Array.isArray(f.news) ||
    !f.news.every(isNews) ||
    !Array.isArray(f.research) ||
    !f.research.every(
      (r) =>
        typeof r.ticker === "string" &&
        typeof r.company === "string" &&
        isDate(r.updatedAt) &&
        typeof r.demo === "boolean" &&
        Array.isArray(r.sourceUrls) &&
        r.sourceUrls.every(isUrl) &&
        isResearch(r.content),
    )
  )
    throw Error("מבנה נתונים לא תקין");
  if (
    !f.demo &&
    (f.updatedAt === null ||
      f.news.some((n) => n.demo) ||
      f.research.some((r) => r.demo))
  )
    throw Error("נתוני הדגמה אינם יכולים להופיע בעדכון אמיתי");
  return f;
}
export async function fetchFeed(): Promise<Feed> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/feed.json`, {
    cache: "no-store",
  });
  if (!response.ok) throw Error("לא ניתן לטעון את העדכון");
  return parseFeed(await response.json());
}
export function isStale(feed: Feed | null, now = Date.now()) {
  return (
    !feed ||
    feed.demo ||
    !feed.updatedAt ||
    Date.parse(feed.updatedAt) - now > 5 * 60 * 1000 ||
    now - Date.parse(feed.updatedAt) > 18 * 60 * 60 * 1000
  );
}
