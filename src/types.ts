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
  publishedAt: string | null;
  collectedAt: string;
  importance: Importance;
  summary: string;
  demo: boolean;
  securityId?: string;
  sourceId?: string;
  documentId?: string;
  sourceName?: string;
  originalTitle?: string;
  filingDate?: string | null;
  classification?: { rule: string; reason: string };
  summaryKind?: "metadata-only";
  publisher?: string;
  discoveryProvider?: "google-news" | "gdelt";
  linkKind?: "google-news-redirect" | "publisher";
  discoveredAt?: string | null;
}
export interface PublicResearch {
  ticker: string;
  company: string;
  updatedAt: string;
  sourceUrls: string[];
  content: Research;
  demo: boolean;
}
export interface LegacyFeed {
  version: 1;
  updatedAt: string | null;
  demo: boolean;
  news: News[];
  research: PublicResearch[];
}
export interface RegistrySecurity {
  id: string;
  name: string;
  ticker: string | null;
  exchange: string | null;
  cik: string | null;
  shareClass: string | null;
  aliases: string[];
  acceptedLegalNames: string[];
  verification: {
    status: "verified" | "unverified";
    date: string | null;
    source: string | null;
    method: string;
  };
  source: {
    id: string;
    kind: "sec-submissions";
    url: string;
    policyUrl: string;
    policyReviewedAt: string;
  } | null;
}
export interface SourceStatus {
  id: string;
  securityId: string;
  name: string;
  url: string | null;
  status: "ok" | "blocked" | "error" | "identity-mismatch" | "no-source";
  lastAttemptAt: string | null;
  lastSuccessfulAt: string | null;
  errorCode: string | null;
  newCount: number;
  availableCount: number;
}
export interface Briefing {
  id: string;
  date: string;
  period: "morning" | "evening";
  timezone: "Asia/Jerusalem";
  generatedAt: string;
  kind: "rule-template";
  status: LiveFeed["status"];
  itemIds: string[];
  bootstrap: boolean;
  noNewItems: boolean;
  failedSourceCount: number;
  questions: string[];
  notice: string;
}
export interface LiveFeed extends Omit<LegacyFeed, "version"> {
  version: 2;
  lastAttemptAt: string;
  lastSuccessfulAt: string | null;
  status: "complete" | "partial" | "failed" | "no-coverage";
  coverage: {
    total: number;
    verified: number;
    working: number;
    uncovered: number;
  };
  sources: SourceStatus[];
  registry: {
    version: 1;
    reviewedAt: string;
    scope: string;
    securities: RegistrySecurity[];
  };
  briefings: Briefing[];
  newCount: number;
  noNewItems: boolean;
  run: { url: string | null; trigger: string };
  limitations: string[];
  articles?: News[];
  discovery?: {
    version: 1;
    lastAttemptAt: string;
    lastSuccessfulAt: string | null;
    status: "complete" | "partial" | "failed";
    newCount: number;
    noNewItems: boolean;
    seenIds: string[];
    registry: {
      companies: {id:string;name:string;displayTicker:string;aliases:string[];query:string;identityVerification:{status:string;date:string;source:string;method:string}}[];
      providers: {id:string;enabled:boolean;notice:string;proofRun:string;proofStatus:string}[];
    };
    sources: {provider:string;securityId:string;name:string;queryUrl:string;status:"results"|"zero-results"|"failed";error:string|null;count:number;newCount:number;rejectedCount:number;lastAttemptAt:string;lastSuccessfulAt:string|null}[];
    briefings: {id:string;generatedAt:string;timezone:string;itemIds:string[];questions:string[]}[];
  };
}
export type Feed = LegacyFeed | LiveFeed;
export interface PersonalState {
  version: 1;
  holdings: Holding[];
  watchlist: Security[];
  research: Record<string, Research>;
  savedNews: News[];
}
