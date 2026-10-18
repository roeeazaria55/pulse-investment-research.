import { useEffect, useRef, type ReactNode } from "react";
import { ArrowUpLeft, Bookmark, ExternalLink, X } from "lucide-react";
import type { News } from "../types";
export const dateTime = (date: string) =>
  new Intl.DateTimeFormat("he-IL", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Jerusalem",
  }).format(new Date(date));
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-orbit">＋</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Section({
  title,
  eyebrow,
  action,
  children,
}: {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="section-head">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    return () => previous?.focus();
  }, []);
  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <dialog
        open
        aria-modal="true"
        className="modal"
        aria-label={title}
        ref={dialog}
        tabIndex={-1}
        onKeyDown={(e) => {
          if (e.key === "Escape") close();
          if (e.key === "Tab") {
            const nodes = e.currentTarget.querySelectorAll<HTMLElement>(
              "button,input,select,textarea,a[href]",
            );
            const first = nodes[0],
              last = nodes[nodes.length - 1];
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }}
      >
        <div className="section-head">
          <h2>{title}</h2>
          <button className="icon-button" onClick={close} aria-label="סגירה">
            <X size={20} />
          </button>
        </div>
        {children}
      </dialog>
    </div>
  );
}
export function NewsCard({
  item,
  saved,
  onSave,
  onResearch,
}: {
  item: News;
  saved: boolean;
  onSave: () => void;
  onResearch: () => void;
}) {
  return (
    <article className="news-card">
      <div className="news-top">
        <div className="company-avatar">{item.ticker.slice(0, 2)}</div>
        <div>
          <b dir="ltr">{item.ticker}</b>
          <small>{item.company}</small>
        </div>
        <span className={`badge ${item.importance}`}>
          {
            { high: "חשיבות גבוהה", medium: "חשיבות בינונית", low: "למעקב" }[
              item.importance
            ]
          }
        </span>
      </div>
      <span className="demo-label">
        {item.demo ? "תוכן הדגמה • אינו דיווח אמיתי" : "מקור חיצוני • יש לאמת"}
      </span>
      <h3>{item.headline}</h3>
      <p>{item.summary}</p>
      {item.classification && (
        <p className="classification-reason">
          <b>מדוע סווג: </b>
          {item.classification.reason}
          <br />
          חשיבות למעקב בלבד — אינה המלצת קנייה.
        </p>
      )}
      <div className="news-dates">
        <span>
          זמן פרסום / קבלה:{" "}
          {item.publishedAt ? dateTime(item.publishedAt) : "לא נמסר במקור"}
        </span>
        {item.filingDate && (
          <span>תאריך הגשה (ללא הנחת שעה): {item.filingDate}</span>
        )}
        <span>נאסף: {dateTime(item.collectedAt)}</span>
        {item.sourceName && <span>מקור: {item.sourceName} • שעון ישראל</span>}
      </div>
      <div className="news-actions">
        <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">
          {item.demo ? "קישור הדגמה" : "מקור"}
          <ExternalLink size={14} />
        </a>
        <button onClick={onResearch}>
          מחקר
          <ArrowUpLeft size={15} />
        </button>
        <button
          aria-pressed={saved}
          className={saved ? "saved" : ""}
          onClick={onSave}
        >
          <Bookmark size={16} fill={saved ? "currentColor" : "none"} />
          {saved ? "נשמר" : "שמירה"}
        </button>
      </div>
    </article>
  );
}
