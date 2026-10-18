import { useState } from "react";
import { initialState } from "../data/initial";
import { isNews, isResearch } from "../data/ingestion";
import type { PersonalState } from "../types";
export const STORAGE_KEY = "pulse.personal.v1";
export function validState(x: unknown): x is PersonalState {
  if (!x || typeof x !== "object") return false;
  const s = x as PersonalState;
  return (
    s.version === 1 &&
    Array.isArray(s.holdings) &&
    s.holdings.every(
      (h) =>
        typeof h.id === "string" &&
        typeof h.name === "string" &&
        typeof h.ticker === "string" &&
        typeof h.thesis === "string" &&
        typeof h.risks === "string" &&
        ["USD", "ILS", "EUR", "GBP"].includes(h.currency) &&
        Number.isFinite(h.allocation) &&
        h.allocation >= 0 &&
        h.allocation <= 100 &&
        Number.isFinite(h.averagePrice) &&
        h.averagePrice >= 0,
    ) &&
    s.holdings.reduce((a, h) => a + h.allocation, 0) <= 100.001 &&
    Array.isArray(s.watchlist) &&
    s.watchlist.every(
      (w) =>
        ["id", "ticker", "name", "category"].every(
          (k) =>
            typeof (w as unknown as Record<string, unknown>)[k] === "string",
        ) && typeof w.verified === "boolean",
    ) &&
    !!s.research &&
    typeof s.research === "object" &&
    !Array.isArray(s.research) &&
    Object.values(s.research).every(isResearch) &&
    Array.isArray(s.savedNews) &&
    s.savedNews.every(isNews)
  );
}
export function readState(): { state: PersonalState; error: string } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { state: initialState(), error: "" };
    const data = JSON.parse(raw);
    if (!validState(data)) throw Error();
    return { state: data, error: "" };
  } catch {
    return {
      state: initialState(),
      error:
        "המידע המקומי אינו זמין או פגום. לא בוצעה כתיבה עליו. ניתן לייצא את המידע המקורי ולבדוק את הגדרות האחסון.",
    };
  }
}
export function usePersonalState() {
  const [initial] = useState(readState);
  const [state, setState] = useState(initial.state);
  const [storageError, setError] = useState(initial.error);
  const update = (next: PersonalState) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setState(next);
      setError("");
      return true;
    } catch {
      setError("השמירה נכשלה. ייתכן שהאחסון מלא או חסום. השינוי לא נשמר.");
      return false;
    }
  };
  return { state, update, storageError };
}
