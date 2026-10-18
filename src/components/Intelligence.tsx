import type { LiveFeed } from "../types";
import { dateTime, Section } from "./UI";
const statusLabel = {
  ok: "זמין ונבדק",
  blocked: "חסום — ללא עקיפה",
  error: "שגיאת מקור",
  "identity-mismatch": "אי התאמת זהות — האיסוף נעצר",
  "no-source": "ללא כיסוי",
};
export function CoveragePanel({ feed }: { feed: LiveFeed }) {
  return (
    <section className="coverage panel" aria-label="מצב איסוף וכיסוי">
      <h2>
        {feed.status === "complete"
          ? "כיסוי מלא"
          : feed.coverage.working
            ? "כיסוי חלקי"
            : "אין מקור פעיל בריצה האחרונה"}
      </h2>
      <p>
        {feed.coverage.working} מתוך {feed.coverage.total} חברות נבדקו בהצלחה.{" "}
        {feed.coverage.uncovered} ללא כיסוי זמין בריצה זו.
      </p>
      <p>
        ניסיון אחרון: {dateTime(feed.lastAttemptAt)} • הצלחה מלאה אחרונה:{" "}
        {feed.lastSuccessfulAt ? dateTime(feed.lastSuccessfulAt) : "טרם הושגה"}
      </p>
      {feed.noNewItems && (
        <div className="alert">
          אין פריטים חדשים במקורות שנבדקו בהצלחה. אין בכך אישור לגבי מקורות
          שנכשלו או חברות ללא כיסוי.
        </div>
      )}
      {feed.status === "failed" && (
        <div className="alert">
          האיסוף נכשל. דיווחים תקינים קודמים נשארים מוצגים עם זמני האיסוף
          המקוריים שלהם.
        </div>
      )}
      <details>
        <summary>פירוט מקורות, זהויות ותאריכי אימות</summary>
        {feed.sources.map((source) => {
          const s = feed.registry.securities.find(
            (s) => s.id === source.securityId,
          )!;
          return (
            <article className="source-status" key={source.id}>
              <h3>
                {s.name} {s.ticker && <b dir="ltr">({s.ticker})</b>}
              </h3>
              <span
                className={`badge ${source.status === "ok" ? "low" : "medium"}`}
              >
                {statusLabel[source.status]}
              </span>
              <p>
                {s.verification.status === "verified"
                  ? `זהות נבדקה: ${s.exchange}, ${s.shareClass}, CIK ${s.cik} • ${s.verification.date}`
                  : "זהות הנייר טרם אומתה; לא נבחר מקור לאיסוף."}
              </p>
              <p>{s.verification.method}</p>
              {s.verification.source && (
                <a
                  className="text-button"
                  href={s.verification.source}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ראיית אימות רשמית
                </a>
              )}
              {source.url && (
                <a
                  className="text-button"
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  מקור SEC
                </a>
              )}
              <p>
                ניסיון:{" "}
                {source.lastAttemptAt
                  ? dateTime(source.lastAttemptAt)
                  : "לא בוצע"}{" "}
                • הצלחה:{" "}
                {source.lastSuccessfulAt
                  ? dateTime(source.lastSuccessfulAt)
                  : "אין"}{" "}
                • {source.newCount} חדשים
              </p>
              {source.errorCode && (
                <small>
                  סיבת כשל: {source.errorCode}. לא הוחלפה בחותמת הצלחה.
                </small>
              )}
            </article>
          );
        })}
      </details>
      {feed.run.url && (
        <a
          className="text-button"
          href={feed.run.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          ריצת האיסוף ב־GitHub Actions
        </a>
      )}
      <small>
        SEC בלבד בשלב זה. לא בוצע ניתוח AI; אין שירות חדשות מסחריות או RSS לא
        מאומת.
      </small>
    </section>
  );
}
export function BriefingPanel({ feed }: { feed: LiveFeed }) {
  const latest = feed.briefings[0];
  if (!latest) return null;
  const render = (b: typeof latest) => (
    <div>
      <p>
        {b.date} • {b.timezone} • הופק: {dateTime(b.generatedAt)}
      </p>
      {b.bootstrap && b.itemIds.length > 0 && (
        <div className="alert">
          אתחול מקור: כולל דיווחים אחרונים מ־30 הימים שקדמו לאיסוף. הם אינם
          מוצגים כאירועים שהתרחשו עכשיו.
        </div>
      )}
      <p>{b.notice}</p>
      {b.noNewItems && <p>אין דיווחים חדשים במקורות שנבדקו בתקופת תדריך זו.</p>}
      {b.failedSourceCount > 0 && (
        <p>חלק מהמקורות נכשלו. יש לעיין בפירוט הכיסוי.</p>
      )}
      {b.itemIds.map((id) => {
        const n = feed.news.find((n) => n.id === id);
        return n ? (
          <article className="briefing-item" key={id}>
            <a href={n.sourceUrl} target="_blank" rel="noopener noreferrer">
              <b>
                {n.ticker} • {n.originalTitle || n.headline}
              </b>
            </a>
            <p>
              {n.sourceName} •{" "}
              {n.publishedAt ? dateTime(n.publishedAt) : "זמן פרסום לא נמסר"}
            </p>
            <p>{n.classification?.reason}</p>
          </article>
        ) : (
          <p key={id}>פריט ישן הוסר מחלון השימור הציבורי.</p>
        );
      })}
      <b>שאלות לבדיקה</b>
      <ul>
        {b.questions.map((q) => (
          <li key={q}>{q}</li>
        ))}
      </ul>
    </div>
  );
  return (
    <Section
      title={`תדריך ${latest.period === "morning" ? "בוקר" : "ערב"} — תבנית דיווחים`}
      eyebrow="מבוסס מקורות ציבוריים"
    >
      {render(latest)}
      {feed.briefings.slice(1, 5).map((b) => (
        <details key={b.id}>
          <summary>
            תדריך {b.period === "morning" ? "בוקר" : "ערב"} • {b.date}
          </summary>
          {render(b)}
        </details>
      ))}
    </Section>
  );
}
