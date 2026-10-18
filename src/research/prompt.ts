import type { News, Research } from "../types";
export const labels = {
  thesis: "תזת השקעה",
  revenue: "צמיחת הכנסות",
  profitability: "רווחיות",
  cashFlow: "תזרים מזומנים",
  valuation: "תמחור",
  advantages: "יתרונות תחרותיים",
  catalysts: "זרזים",
  risks: "סיכונים",
  bear: "תרחיש דובי",
  base: "תרחיש בסיס",
  bull: "תרחיש שורי",
};
export function buildPrompt(
  name: string,
  ticker: string,
  research: Research,
  news: News[],
  sources: string[] = [],
) {
  return `נתח בעברית את ${name} (${ticker || "סימול טרם אומת"}). זהו מחקר אישי ולא ייעוץ השקעות.\nהפרד עובדות, הנחות ומידע חסר. אל תמציא נתונים. בדוק תאריכים ומקורות, הצג טיעון נגדי ותרחישי דוב/בסיס/שור.\n\n${Object.entries(
    labels,
  )
    .map(
      ([k, label]) =>
        `${label}: ${research[k as keyof typeof labels] || "טרם הוזן"}`,
    )
    .join(
      "\n",
    )}\n\nהערות היסטוריות:\n${research.notes.map((n) => `${n.createdAt}: ${n.text}`).join("\n") || "אין"}\n\nפריטים רלוונטיים (הדגמות אינן חדשות אמיתיות):\n${news.map((n) => `[${n.demo ? "הדגמה בלבד" : "מקור לבדיקה"}] ${n.headline}\nפורסם: ${n.publishedAt}; נאסף: ${n.collectedAt}\n${n.summary}\n${n.sourceUrl}`).join("\n\n") || "אין פריטים"}\n\nמקורות נוספים:\n${sources.join("\n") || "אין"}\n\nהתחל במידע החסר, נתח השפעה על התזה, סיכונים ושאלות לבדיקה. אם אין לך גישה למקור, ציין זאת במפורש.`;
}
export async function copyText(text: string) {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      /* fallback below */
    }
  }
  const active = document.activeElement as HTMLElement | null;
  const area = document.createElement("textarea");
  area.value = text;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  } finally {
    area.remove();
    active?.focus();
  }
  return copied;
}
