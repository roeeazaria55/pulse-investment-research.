// @vitest-environment jsdom
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import App from "../src/App";
import fixture from "./fixtures/demo-feed.json";
beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }),
  );
  vi.stubGlobal("scrollTo", vi.fn());
  vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const nav = (name: string) =>
  fireEvent.click(
    within(screen.getByRole("navigation", { name: "ניווט נייד" })).getByRole(
      "button",
      { name },
    ),
  );
describe("application user flows", () => {
  it("navigates, creates/edits/deletes holdings and persists after reload", async () => {
    const view = render(<App />);
    await screen.findByText("מצב הדגמה");
    nav("תיק השקעות");
    expect(screen.getByText("כל השקעה מתחילה בתזה")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "הוספת אחזקה" }));
    fireEvent.change(screen.getByLabelText("סימול"), {
      target: { value: "TEST" },
    });
    fireEvent.change(screen.getByLabelText("שם החברה"), {
      target: { value: "Test Company" },
    });
    fireEvent.change(screen.getByLabelText(/הקצאה באחוזים/), {
      target: { value: "25" },
    });
    fireEvent.change(screen.getByLabelText("מחיר רכישה ממוצע"), {
      target: { value: "12.5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "שמירת אחזקה" }));
    expect(screen.getByText("TEST")).toBeTruthy();
    view.unmount();
    render(<App />);
    nav("תיק השקעות");
    expect(screen.getByText("Test Company")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "עריכה" }));
    fireEvent.change(screen.getByLabelText("שם החברה"), {
      target: { value: "Edited Company" },
    });
    fireEvent.click(screen.getByRole("button", { name: "שמירת אחזקה" }));
    expect(screen.getByText("Edited Company")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "מחיקת TEST" }));
    expect(screen.getByText("כל השקעה מתחילה בתזה")).toBeTruthy();
  });
  it("filters and saves demo news for research", async () => {
    render(<App />);
    await screen.findByText("מצב הדגמה");
    nav("חדשות");
    fireEvent.change(screen.getByLabelText("חיפוש חדשות"), {
      target: { value: "NBIS" },
    });
    expect(screen.getAllByRole("article")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "שמירה" }));
    fireEvent.change(screen.getByLabelText("חיפוש חדשות"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("מקור הפריטים"), {
      target: { value: "saved" },
    });
    expect(screen.getAllByRole("article")).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: "נשמר" }).getAttribute("aria-pressed"),
    ).toBe("true");
  });
  it("saves research, creates a dated note and prepares an editable prompt", async () => {
    render(<App />);
    await screen.findByText("מצב הדגמה");
    nav("מחקר");
    fireEvent.change(screen.getByLabelText("תזת השקעה"), {
      target: { value: "A private investment hypothesis" },
    });
    fireEvent.click(screen.getByRole("button", { name: "שמירת מחקר" }));
    fireEvent.change(screen.getByLabelText("הערה חדשה"), {
      target: { value: "Recheck the source" },
    });
    fireEvent.click(screen.getByRole("button", { name: "הוספת הערה" }));
    fireEvent.click(screen.getByRole("button", { name: "הכנת בקשת ניתוח" }));
    const area = screen.getByLabelText("טקסט להעתקה") as HTMLTextAreaElement;
    expect(area.value).toContain("A private investment hypothesis");
    expect(area.value).toContain("Recheck the source");
    expect(area.value).toContain(
      "https://example.com/pulse-demo/infrastructure",
    );
    expect(
      screen.getByRole("link", { name: "פתיחת ChatGPT" }).getAttribute("href"),
    ).toBe("https://chatgpt.com/");
  });
  it("adds, categorizes, edits and removes watchlist companies", async () => {
    render(<App />);
    await screen.findByText("מצב הדגמה");
    nav("מעקב");
    expect(screen.getAllByRole("article")).toHaveLength(11);
    fireEvent.click(screen.getByRole("button", { name: "הוספת חברה" }));
    fireEvent.change(screen.getByLabelText("שם החברה"), {
      target: { value: "Test Watch" },
    });
    fireEvent.change(screen.getByLabelText("סימול מוצע (אופציונלי)"), {
      target: { value: "TW" },
    });
    fireEvent.change(screen.getByLabelText("קטגוריה"), {
      target: { value: "בדיקה" },
    });
    fireEvent.click(screen.getByRole("button", { name: "שמירת חברה" }));
    fireEvent.change(screen.getByLabelText("סינון קטגוריה"), {
      target: { value: "בדיקה" },
    });
    expect(screen.getAllByRole("article")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "עריכת Test Watch" }));
    fireEvent.change(screen.getByLabelText("שם החברה"), {
      target: { value: "Edited Watch" },
    });
    fireEvent.click(screen.getByRole("button", { name: "שמירת חברה" }));
    expect(screen.getByText("Edited Watch")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "הסרת Edited Watch" }));
    await waitFor(() => expect(screen.queryByText("Edited Watch")).toBeNull());
  });
});
