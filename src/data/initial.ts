import type { Research, Security, PersonalState } from "../types";
export const blankResearch = (): Research => ({
  thesis: "",
  revenue: "",
  profitability: "",
  cashFlow: "",
  valuation: "",
  advantages: "",
  catalysts: "",
  risks: "",
  bear: "",
  base: "",
  bull: "",
  notes: [],
});
export const initialWatchlist: Security[] = [
  ["NBIS", "Nebius", "תשתיות AI"],
  ["META", "Meta Platforms", "טכנולוגיה"],
  ["DLO", "dLocal", "פינטק"],
  ["FTAI", "FTAI Aviation", "תעופה"],
  ["LMND", "Lemonade", "פינטק"],
  ["SNDK", "SanDisk", "טכנולוגיה"],
  ["IREN", "IREN", "תשתיות AI"],
  ["", "Next Vision", "ישראל"],
  ["", "Enlight Renewable Energy", "אנרגיה"],
  ["", "BrainsWay", "בריאות"],
  ["", "Gilat Telecom", "ישראל"],
].map(([ticker, name, category], i) => ({
  id: `initial-${i}`,
  ticker,
  name,
  category,
  verified: false,
}));
export const initialState = (): PersonalState => ({
  version: 1,
  holdings: [],
  watchlist: initialWatchlist,
  research: {},
  savedNews: [],
});
