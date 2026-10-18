import { SourceError } from "./network.mjs";
const iso = (x) =>
  typeof x === "string" &&
  /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(x) &&
  Number.isFinite(Date.parse(x));
const norm = (x) =>
  String(x)
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
export function verifyIdentity(security, data) {
  if (
    security.verification.status !== "verified" ||
    !security.source ||
    !/^\d{10}$/.test(security.cik || "")
  )
    throw new SourceError("unverified-identity");
  if (
    String(data?.cik).padStart(10, "0") !== security.cik ||
    !security.acceptedLegalNames.some((n) => norm(n) === norm(data?.name))
  )
    throw new SourceError("identity-mismatch");
  if (
    !Array.isArray(data.tickers) ||
    !Array.isArray(data.exchanges) ||
    data.tickers.length !== data.exchanges.length
  )
    throw new SourceError("identity-mismatch");
  if (
    !data.tickers.some(
      (ticker, i) =>
        ticker === security.ticker &&
        norm(data.exchanges[i]) === norm(security.exchange),
    )
  )
    throw new SourceError("identity-mismatch");
}
export function classify(form) {
  if (/^(10-K|10-Q|20-F|40-F)(\/A)?$/.test(form))
    return {
      importance: "high",
      rule: "periodic-report-v1",
      reason:
        "דיווח כספי תקופתי לפי סוג הטופס; יש לבדוק את הדוח ואת השינויים מול התקופה הקודמת.",
    };
  if (/^(8-K|6-K)(\/A)?$/.test(form))
    return {
      importance: "medium",
      rule: "current-report-v1",
      reason:
        "דיווח שוטף לפי סוג הטופס. תוכן הדיווח לא נותח; אין הנחה שכל דיווח מהותי באותה מידה.",
    };
  return {
    importance: "low",
    rule: "other-filing-v1",
    reason: "דיווח ציבורי אחר; רמת המעקב נקבעה לפי סוג הטופס בלבד.",
  };
}
export function parseSubmissions(security, data, collectedAt) {
  verifyIdentity(security, data);
  const r = data.filings?.recent;
  if (
    !r ||
    !Array.isArray(r.accessionNumber) ||
    r.accessionNumber.length > 10000
  )
    throw new SourceError("malformed-feed");
  for (const k of ["form", "filingDate", "primaryDocument"])
    if (!Array.isArray(r[k]) || r[k].length !== r.accessionNumber.length)
      throw new SourceError("malformed-feed");
  if (
    r.acceptanceDateTime !== undefined &&
    (!Array.isArray(r.acceptanceDateTime) ||
      r.acceptanceDateTime.length !== r.accessionNumber.length)
  )
    throw new SourceError("malformed-feed");
  if (
    r.primaryDocDescription !== undefined &&
    (!Array.isArray(r.primaryDocDescription) ||
      r.primaryDocDescription.length !== r.accessionNumber.length)
  )
    throw new SourceError("malformed-feed");
  return r.accessionNumber.map((accession, i) => {
    const form = r.form[i],
      document = r.primaryDocument[i],
      date = r.filingDate[i];
    if (
      typeof accession !== "string" ||
      !/^\d{10}-\d{2}-\d{6}$/.test(accession) ||
      typeof form !== "string" ||
      !/^[A-Za-z0-9 /-]{1,40}$/.test(form) ||
      typeof document !== "string" ||
      document.length > 180 ||
      !/^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(document) ||
      document.includes("..") ||
      !(
        date === "" ||
        date === null ||
        (typeof date === "string" &&
          /^\d{4}-\d{2}-\d{2}$/.test(date) &&
          Number.isFinite(Date.parse(date)))
      )
    )
      throw new SourceError("malformed-feed");
    const publishedAt = iso(r.acceptanceDateTime?.[i])
      ? new Date(r.acceptanceDateTime[i]).toISOString()
      : null;
    // A filing date is not an exact publication timestamp. Never append midnight.
    const description = r.primaryDocDescription?.[i];
    if (
      description !== undefined &&
      (typeof description !== "string" || description.length > 1500)
    )
      throw new SourceError("malformed-feed");
    const title = description?.trim() ? description : form;
    const c = classify(form);
    return {
      id: `sec:${security.cik}:${accession}`,
      securityId: security.id,
      sourceId: security.source.id,
      documentId: accession,
      sourceName: "SEC EDGAR submissions",
      ticker: security.ticker,
      company: security.name,
      headline: title,
      originalTitle: title,
      titleOrigin: description?.trim() ? "primaryDocDescription" : "form",
      sourceUrl: `https://www.sec.gov/Archives/edgar/data/${Number(security.cik)}/${accession.replaceAll("-", "")}/${document}`,
      publishedAt,
      publicationTimeBasis: publishedAt ? "SEC acceptanceDateTime" : "unknown",
      filingDate: date || null,
      collectedAt,
      importance: c.importance,
      classification: { rule: c.rule, reason: c.reason },
      form,
      summary: `מטא־נתונים מ־SEC EDGAR: הוגש טופס ${form}${date ? ` בתאריך ${date}` : ""}, מסמך ${accession}. לא בוצע ניתוח תוכן או ניתוח AI.`,
      summaryKind: "metadata-only",
      demo: false,
    };
  });
}
export function briefingSlot(now) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Jerusalem",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(now))
      .filter((p) => p.type !== "literal")
      .map((p) => [p.type, p.value]),
  );
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    period: Number(parts.hour) >= 17 ? "evening" : "morning",
    timezone: "Asia/Jerusalem",
  };
}
export function deduplicate(items) {
  const map = new Map();
  for (const item of items) {
    const old = map.get(item.id);
    map.set(item.id, old ? { ...item, collectedAt: old.collectedAt } : item);
  }
  return [...map.values()].sort(
    (a, b) =>
      (b.publishedAt || b.filingDate || "").localeCompare(
        a.publishedAt || a.filingDate || "",
      ) || a.id.localeCompare(b.id),
  );
}
export async function collect({
  registry,
  previous = null,
  state = { version: 1, seen: [], briefings: [] },
  getJson,
  now = new Date().toISOString(),
  runUrl = null,
  trigger = "manual",
}) {
  const prior = previous?.version === 2 ? previous : null;
  const priorSources = new Map(
    (prior?.sources || []).map((s) => [s.securityId, s]),
  );
  let news = [...(prior?.news || [])];
  const seen = new Set(state.seen || []);
  const newItems = [];
  const sources = [];
  for (const s of registry.securities) {
    const before = priorSources.get(s.id);
    const record = {
      id: s.source?.id || `none-${s.id}`,
      securityId: s.id,
      name: s.source ? "SEC EDGAR submissions" : "ללא מקור מאומת",
      url: s.source?.url || null,
      status: "no-source",
      lastAttemptAt: null,
      lastSuccessfulAt: before?.lastSuccessfulAt || null,
      errorCode: null,
      newCount: 0,
      availableCount: 0,
    };
    if (
      s.verification.status === "verified" &&
      s.source?.kind === "sec-submissions"
    ) {
      record.lastAttemptAt = now;
      try {
        const data = await getJson(s.source.url);
        const parsed = deduplicate(parseSubmissions(s, data, now));
        // On first successful source load, bootstrap up to 30 reports from the last 30 days.
        // The rest are recorded as seen so old history will not become "new" later.
        const bootstrap = !before?.lastSuccessfulAt;
        const fresh = parsed.filter((n) => !seen.has(n.id));
        const selected = bootstrap
          ? fresh
              .filter(
                (n) =>
                  !n.filingDate ||
                  Date.parse(n.filingDate) >= Date.parse(now) - 30 * 86400000,
              )
              .slice(0, 30)
          : fresh;
        for (const n of parsed) seen.add(n.id);
        newItems.push(...selected);
        news.push(...selected);
        record.status = "ok";
        record.lastSuccessfulAt = now;
        record.newCount = selected.length;
        record.availableCount = parsed.length;
      } catch (e) {
        record.status =
          e.code === "blocked"
            ? "blocked"
            : e.code === "identity-mismatch"
              ? "identity-mismatch"
              : "error";
        record.errorCode =
          e instanceof SourceError ? e.code : "unexpected-source-error";
      }
    }
    sources.push(record);
  }
  news = deduplicate(news).slice(0, 600);
  const ok = sources.filter((s) => s.status === "ok").length;
  const eligible = registry.securities.filter(
    (s) => s.verification.status === "verified" && s.source,
  ).length;
  const all = ok === registry.securities.length && ok > 0;
  const status = all
    ? "complete"
    : ok > 0
      ? "partial"
      : eligible
        ? "failed"
        : "no-coverage";
  const lastSuccessfulAt = all ? now : prior?.lastSuccessfulAt || null;
  const slot = briefingSlot(now);
  const slotId = `${slot.date}:${slot.period}`;
  const existing = (prior?.briefings || []).find((b) => b.id === slotId);
  const ids = [
    ...new Set([...(existing?.itemIds || []), ...newItems.map((n) => n.id)]),
  ];
  const briefing = {
    id: slotId,
    ...slot,
    generatedAt: now,
    kind: "rule-template",
    status,
    itemIds: ids,
    bootstrap:
      existing?.bootstrap ?? !prior?.sources.some((s) => s.lastSuccessfulAt),
    noNewItems: ids.length === 0 && ok > 0,
    failedSourceCount: sources.filter((s) =>
      ["error", "blocked", "identity-mismatch"].includes(s.status),
    ).length,
    questions: [
      "מה השתנה לעומת הדיווח הקודם?",
      "אילו נתונים דורשים קריאת המקור המלא?",
      "האם הדיווח משנה הנחה בתזת ההשקעה?",
    ],
    notice:
      "תדריך תבנית המבוסס על מטא־נתונים; לא ניתוח AI ולא המלצת קנייה. בריצה ראשונה נכללים דיווחים אחרונים לצורך אתחול, לא אירועים חדשים בזמן אמת.",
  };
  const briefings = [
    briefing,
    ...(prior?.briefings || []).filter((b) => b.id !== slotId),
  ].slice(0, 28);
  const feed = {
    version: 2,
    demo: false,
    updatedAt: lastSuccessfulAt,
    lastAttemptAt: now,
    lastSuccessfulAt,
    status,
    newCount: newItems.length,
    noNewItems: newItems.length === 0 && ok > 0,
    coverage: {
      total: registry.securities.length,
      verified: eligible,
      working: ok,
      uncovered: registry.securities.length - ok,
    },
    sources,
    registry,
    news,
    research: prior?.research || [],
    briefings,
    run: { url: runUrl, trigger },
    limitations: [
      "SEC submissions metadata only; no article or filing text scraping.",
      "Source availability is verified independently on each run.",
      "Recent submissions only; older historical files are not crawled.",
    ],
  };
  return {
    feed,
    state: {
      version: 1,
      seen: [...seen].sort(),
      briefings: briefings.map((b) => b.id),
    },
  };
}
