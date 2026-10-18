export type Importance = "high" | "medium" | "low";
export interface Security {
  id: string;
  ticker: string;
  name: string;
  category: string;
  verified: boolean;
}
export interface Holding {
  id: string;
  ticker: string;
  name: string;
  allocation: number;
  averagePrice: number;
  currency: string;
  thesis: string;
  risks: string;
}
export const researchFields = [
  "thesis",
  "revenue",
  "profitability",
  "cashFlow",
  "valuation",
  "advantages",
  "catalysts",
  "risks",
  "bear",
  "base",
  "bull",
] as const;
export type ResearchField = (typeof researchFields)[number];
export interface Note {
  id: string;
  createdAt: string;
  text: string;
}
export type Research = Record<ResearchField, string> & { notes: Note[] };
export interface News {
  id: string;
  ticker: string;
  company: string;
  headline: string;
  sourceUrl: string;
  publishedAt: string;
  collectedAt: string;
  importance: Importance;
  summary: string;
  demo: boolean;
}
export interface PublicResearch {
  ticker: string;
  company: string;
  updatedAt: string;
  sourceUrls: string[];
  content: Research;
  demo: boolean;
}
export interface Feed {
  version: 1;
  updatedAt: string | null;
  demo: boolean;
  news: News[];
  research: PublicResearch[];
}
export interface PersonalState {
  version: 1;
  holdings: Holding[];
  watchlist: Security[];
  research: Record<string, Research>;
  savedNews: News[];
}
