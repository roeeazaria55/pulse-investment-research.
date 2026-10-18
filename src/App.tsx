import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowUpLeft,
  Bell,
  BookOpen,
  Check,
  ChevronLeft,
  Download,
  ExternalLink,
  Home,
  ListFilter,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Star,
  Trash2,
  Wallet,
  Newspaper,
  Copy,
  Pencil,
  WifiOff,
} from "lucide-react";
import { usePersonalState, STORAGE_KEY } from "./state/storage";
import { blankResearch } from "./data/initial";
import { fetchFeed, isStale } from "./data/ingestion";
import { buildPrompt, copyText, labels } from "./research/prompt";
import { Empty, Modal, NewsCard, Section, dateTime } from "./components/UI";
import { CoveragePanel, BriefingPanel } from "./components/Intelligence";
import { resolveSecurity } from "./data/feedV2";
import { DiscoveryPanel, WebNewsSearch } from "./components/Discovery";
import {DailyPanel,CalendarPanel,NotificationsPanel} from './components/PhaseThree';
import { OfficialSources } from "./components/OfficialSources";
import { ResearchExchange } from "./components/ResearchExchange";
import { officialCompany } from "./data/official";
import type { Feed, Holding, News, Research, Security } from "./types";

const tabs = [
  { id: "home", label: "בית", icon: Home },
  { id: "portfolio", label: "תיק השקעות", icon: Wallet },
  { id: "news", label: "חדשות", icon: Newspaper },
  { id: "research", label: "מחקר", icon: BookOpen },
  { id: "watchlist", label: "מעקב", icon: Star },
] as const;
type Tab = (typeof tabs)[number]["id"];
type InstallEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: string }>;
};
const uid = () => crypto.randomUUID();
const nameOf = (s: Security) => s.ticker || s.name;
export default function App() {
  const { state, update, storageError } = usePersonalState();
  const [tab, setTab] = useState<Tab>("home");
  const [feed, setFeed] = useState<Feed | null>(null);
  const [feedError, setFeedError] = useState("");
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(Date.now());
  const [online, setOnline] = useState(navigator.onLine);
  const [toast, setToast] = useState("");
  const [query, setQuery] = useState("");
  const [importance, setImportance] = useState("all");
  const [companyFilter,setCompanyFilter]=useState('all');
  const [industryFilter,setIndustryFilter]=useState('all');
  const [periodFilter,setPeriodFilter]=useState('all');
  const [readFilter,setReadFilter]=useState('all');
  const [readIds,setReadIds]=useState<string[]>(()=>{try{const x=JSON.parse(localStorage.getItem('pulse-read-news-v1')||'[]');return Array.isArray(x)?x.filter(v=>typeof v==='string'):[];}catch{return [];}});
  const [deepLink,setDeepLink]=useState(()=>location.hash);
  const [newsScope, setNewsScope] = useState("all");
  const [category, setCategory] = useState("all");
  const [holdingEdit, setHoldingEdit] = useState<Holding | null | undefined>();
  const [watchEdit, setWatchEdit] = useState<Security | null | undefined>();
  const [selected, setSelected] = useState("initial-0");
  const [draft, setDraft] = useState<Research>(blankResearch());
  const [dirty, setDirty] = useState(false);
  const [note, setNote] = useState("");
  const [prompt, setPrompt] = useState<string | null>(null);
  const [install, setInstall] = useState<InstallEvent | null>(null);
  const [help, setHelp] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const allSecurities = [
    ...state.watchlist,
    ...state.holdings
      .filter((h) => !state.watchlist.some((w) => w.ticker === h.ticker))
      .map((h) => ({
        id: h.id,
        ticker: h.ticker,
        name: h.name,
        category: "תיק",
        verified: false,
      })),
  ];
  for (const company of [...(feed?.research || []), ...(feed?.news || [])]) {
    if (!allSecurities.some((s) => company.ticker ? s.ticker === company.ticker : s.name === company.company)) {
      allSecurities.push({
        id: `public-${company.ticker || company.company}`,
        ticker: company.ticker,
        name: company.company,
        category: "מקורות ציבוריים",
        verified: false,
      });
    }
  }
  const security =
    allSecurities.find((s) => s.id === selected) || allSecurities[0];
  const researchKey = security
    ? (security.ticker || security.name).toUpperCase()
    : "";
  const publicResearch = feed?.research.find(
    (r) => r.ticker.toUpperCase() === researchKey,
  );
  const stored = state.research[researchKey];
  const notify = (message: string) => setToast(message);
  const refresh = async () => {
    setLoading(true);
    try {
      const f = await fetchFeed();
      setFeed(f);
      setFeedError("");
    } catch {
      setFeedError("לא ניתן לקבל עדכון. המידע האחרון נשאר מוצג, אם קיים.");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void refresh();
    const timer = setInterval(() => setNow(Date.now()), 60000);
    const connectivity = () => setOnline(navigator.onLine);
    const offer = (e: Event) => {
      e.preventDefault();
      setInstall(e as InstallEvent);
    };
    window.addEventListener("online", connectivity);
    window.addEventListener("offline", connectivity);
    window.addEventListener("beforeinstallprompt", offer);
    return () => {
      clearInterval(timer);
      window.removeEventListener("online", connectivity);
      window.removeEventListener("offline", connectivity);
      window.removeEventListener("beforeinstallprompt", offer);
    };
  }, []);
  useEffect(() => {
    // A refreshed public profile must never erase unsaved personal edits.
    if (dirty) return;
    setDraft(stored || publicResearch?.content || blankResearch());
    setDirty(false);
    setNote("");
  }, [researchKey, stored, publicResearch]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    if (!dirty) return;
    const leave = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", leave);
    return () => window.removeEventListener("beforeunload", leave);
  }, [dirty]);
  const persistResearch = () => {
    if (!researchKey) return false;
    const ok = update({
      ...state,
      research: { ...state.research, [researchKey]: draft },
    });
    if (ok) {
      setDirty(false);
      notify("המחקר נשמר במכשיר");
    }
    return ok;
  };
  const navigate = (next: Tab) => {
    if (dirty && !persistResearch()) return;
    setTab(next);
    setQuery("");
    window.scrollTo({ top: 0, behavior: "smooth" });
    requestAnimationFrame(() => heading.current?.focus());
  };
  const openResearch = (ticker: string) => {
    if (dirty && !persistResearch()) return;
    const target = allSecurities.find((s) => s.ticker === ticker || s.name === ticker);
    if (target) setSelected(target.id);
    navigate("research");
  };
  const saveNews = (item: News) => {
    const exists = state.savedNews.some((n) => n.id === item.id);
    if (
      update({
        ...state,
        savedNews: exists
          ? state.savedNews.filter((n) => n.id !== item.id)
          : [item, ...state.savedNews],
      })
    )
      notify(exists ? "הפריט הוסר מהמחקר" : "הפריט נשמר למחקר");
  };
  const toggleRead=(id:string)=>{
    const next=readIds.includes(id)?readIds.filter(x=>x!==id):[...readIds,id];
    try{localStorage.setItem('pulse-read-news-v1',JSON.stringify(next));setReadIds(next);}catch{notify('לא ניתן לשמור מצב קריאה במכשיר');}
  };
  useEffect(()=>{
    const apply=()=>{const hash=location.hash;setDeepLink(hash);const p=new URLSearchParams(hash.slice(1));
      if(p.has('news')){setTab('news');setNewsScope('all');setImportance('all');setCompanyFilter('all');setIndustryFilter('all');setReadFilter('all');setPeriodFilter('all');setQuery('');}
      else if(p.has('earnings')||p.has('results')||p.has('briefing')||p.has('notifications'))setTab('home');
    };apply();window.addEventListener('hashchange',apply);return()=>window.removeEventListener('hashchange',apply);
  },[]);
  useEffect(()=>{
    const p=new URLSearchParams(deepLink.slice(1));const key=['news','earnings','results','briefing'].find(k=>p.has(k));
    if(!key)return;const id=key==='news'?`news-${p.get(key)}`:key==='briefing'?`briefing-${p.get(key)}`:`${key}-${p.get(key)}`;
    requestAnimationFrame(()=>document.getElementById(id)?.scrollIntoView({block:'center'}));
  },[deepLink,feed]);
  const news = (
    newsScope === "saved" ? state.savedNews : feed?.news || []
  ).filter(
    (n) =>
      (!(
        feed?.version === 2 && ["watchlist", "portfolio"].includes(newsScope)
      ) ||
        (newsScope === "watchlist" ? state.watchlist : state.holdings).some(
          (s) => resolveSecurity(feed, s)?.id === n.securityId,
        )) &&
      (importance === "all" || n.importance === importance) &&
      (companyFilter==='all'||n.securityId===companyFilter) &&
      (industryFilter==='all'||(feed?.version===2&&!!n.securityId&&feed.intelligence?.industries.config.companyIndustries[n.securityId]?.includes(industryFilter))) &&
      (periodFilter==='all'||(!!n.publishedAt&&now-Date.parse(n.publishedAt)>=0&&now-Date.parse(n.publishedAt)<=86400000)) &&
      (readFilter==='all'||(readFilter==='read'?readIds.includes(n.id):!readIds.includes(n.id))) &&
      `${n.headline} ${n.company} ${n.ticker} ${n.summary}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const allocation = state.holdings.reduce((sum, h) => sum + h.allocation, 0);
  const stale = isStale(feed, now);
  const related = [
    ...new Map(
      [...(feed?.news || []), ...state.savedNews]
        .filter((n) => security && (n.ticker ? n.ticker === security.ticker : n.company === security.name))
        .map((n) => [n.id, n]),
    ).values(),
  ];
  const exportData = () => {
    const raw = localStorage.getItem(STORAGE_KEY) || JSON.stringify(state);
    const url = URL.createObjectURL(
      new Blob([raw], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "pulse-private-backup.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        דילוג לתוכן
      </a>
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            navigate("home");
          }}
        >
          <span className="brand-mark">
            <Activity size={25} />
          </span>
          <span>
            PULSE<small>INVESTMENT INTELLIGENCE</small>
          </span>
        </a>
        <span className="nav-caption">סביבת המחקר שלך</span>
        <nav aria-label="ניווט ראשי" className="desktop-nav">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => navigate(t.id)}
              aria-current={tab === t.id ? "page" : undefined}
              className={tab === t.id ? "active" : ""}
            >
              <t.icon size={20} />
              {t.label}
              {tab === t.id && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <ShieldCheck size={20} />
          <b>המחקר שלך. במכשיר שלך.</b>
          <p>התיק וההערות נשמרים מקומית בדפדפן.</p>
          <button className="text-button" onClick={exportData}>
            <Download size={15} />
            ייצוא גיבוי אישי
          </button>
        </div>
        <small className="version">PULSE / VERSION 3.0 PREVIEW</small>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="mobile-brand">
            <Activity size={23} />
            <b>PULSE</b>
          </div>
          <div className="breadcrumb">
            סביבת עבודה אישית <ChevronLeft size={14} />{" "}
            <b>{tabs.find((t) => t.id === tab)?.label}</b>
          </div>
          <div className="topbar-actions">
            <span className="local-tag">
              <span /> מקומי ופרטי
            </span>
            <button
              className="icon-button"
              onClick={() => setHelp(true)}
              aria-label="התקנת האפליקציה"
            >
              <Download size={19} />
            </button>
            <button
              className="icon-button"
              onClick={() => navigate("news")}
              aria-label="פתיחת חדשות"
            >
              <Bell size={19} />
            </button>
            <span className="profile">P</span>
          </div>
        </header>
        <main id="main" className={feed?.version===2&&feed.intelligence?'phase3':undefined}>
          <div className="page-heading">
            <div>
              <div className="eyebrow">היתרון שלך מתחיל במחקר טוב</div>
              <h1 ref={heading} tabIndex={-1}>
                {
                  {
                    home: feed?.version===2&&feed.intelligence?"התדריך היומי.":"התמונה הגדולה.",
                    portfolio: "תיק ההשקעות שלי.",
                    news: "מה חשוב לדעת.",
                    research: "מעבר לכותרת.",
                    watchlist: "על הרדאר שלי.",
                  }[tab]
                }
              </h1>
              <p>
                {
                  {
                    home: "כל מה שחשוב להשקעות שלך, במקום אחד.",
                    portfolio: "התזה, ההקצאה והסיכון — תמונה אישית של ההחזקות.",
                    news: "מקורות, הקשר ותובנות. בלי הרעש.",
                    research: "מרחב עבודה לתזה הבאה שלך.",
                    watchlist: "חברות מעניינות. הזדמנויות למחקר.",
                  }[tab]
                }
              </p>
            </div>
            <button
              className="secondary refresh"
              onClick={() => void refresh()}
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "spin" : ""} />
              {loading ? "טוען…" : "רענון מידע"}
            </button>
          </div>
          <div className="data-status" role="status">
            <span className="status-light" />
            <span>
              {feed?.demo
                ? "מצב הדגמה"
                : feed
                  ? "נתונים ציבוריים"
                  : "ממתין לנתונים"}
            </span>
            <span className="status-divider" />
            <span>
              {feed?.version === 2
                ? `ניסיון איסוף: ${dateTime(feed.lastAttemptAt)}`
                : feed?.updatedAt
                  ? `עדכון נתונים מוצלח: ${dateTime(feed.updatedAt)}`
                  : "טרם התקבל עדכון נתונים אמיתי"}
            </span>
            <span className="status-warning">
              {stale
                ? "המידע אינו עדכני"
                : feed?.version === 2 && (feed.discovery ? feed.discovery.status !== "complete" : feed.status !== "complete")
                  ? "כיסוי חלקי — פירוט המקורות להלן"
                  : "הנתונים עודכנו ב־18 השעות האחרונות"}
            </span>
          </div>
          {!online && (
            <div className="alert">
              <WifiOff size={17} />
              אין חיבור לרשת. ניתן להמשיך לעבוד עם המידע המקומי.
            </div>
          )}
          {feedError && <div className="alert">{feedError}</div>}
          {storageError && (
            <div className="alert error" role="alert">
              {storageError}
              <button onClick={exportData}>ייצוא המידע המקורי</button>
            </div>
          )}
          {feed?.version===2&&feed.intelligence&&tab==='home'&&<><DailyPanel intel={feed.intelligence} news={feed.news} date={new URLSearchParams(deepLink.slice(1)).get('briefing')||undefined}/><CalendarPanel intel={feed.intelligence} focus={new URLSearchParams(deepLink.slice(1)).get('results')||undefined}/><NotificationsPanel open={deepLink.includes('notifications=')}/></>}
          {feed?.version === 2 &&
            ["home", "news", "watchlist"].includes(tab) && (
              <>{feed.intelligence?<details className="panel"><summary>מצב איסוף חדשות ומקורות</summary><DiscoveryPanel feed={feed}/><CoveragePanel feed={feed}/></details>:<><DiscoveryPanel feed={feed}/><CoveragePanel feed={feed}/></>}</>
            )}
          {tab === "home" && (
            <>
              <div className="overview-grid">
                <section className="briefing">
                  <div className="briefing-top">
                    <span className="briefing-icon">
                      <Activity size={22} />
                    </span>
                    <span>THE DAILY PULSE</span>
                    <span className="badge">
                      {feed?.version === 2
                        ? feed.discovery ? "כותרות מהרשת • תבנית" : "דיווחי SEC • תבנית"
                        : "תדריך הדגמה"}
                    </span>
                  </div>
                  <h2>
                    פחות רעש.
                    <br />
                    <em>יותר פרספקטיבה.</em>
                  </h2>
                  <p>
                    תדריך המחקר שלך מתחיל כאן. רכזו את ההתפתחויות החשובות, בדקו
                    מה השתנה בתזה והחליטו מה לחקור לעומק.
                  </p>
                  <div className="briefing-bottom">
                    <button
                      className="primary"
                      onClick={() => navigate("news")}
                    >
                      לפתיחת התדריך <ArrowUpLeft size={18} />
                    </button>
                    <small>
                      {feed?.version === 2
                        ? "תדריכי בוקר וערב • שעון ישראל"
                        : "תדריך בוקר / ערב יחובר בשלב הבא"}
                    </small>
                  </div>
                  <div className="briefing-art" aria-hidden="true">
                    <div />
                    <div />
                    <div />
                    <Activity />
                  </div>
                </section>
                <Section title="במבט אחד" eyebrow="סביבת העבודה">
                  <div className="stat-row">
                    <span className="stat-icon">
                      <Wallet />
                    </span>
                    <div>
                      <small>חברות בתיק</small>
                      <strong>
                        {state.holdings.length.toString().padStart(2, "0")}
                      </strong>
                    </div>
                    <button
                      aria-label="מעבר לתיק ההשקעות"
                      onClick={() => navigate("portfolio")}
                    >
                      <ArrowUpLeft />
                    </button>
                  </div>
                  <div className="stat-row">
                    <span className="stat-icon">
                      <Star />
                    </span>
                    <div>
                      <small>ברשימת המעקב</small>
                      <strong>
                        {state.watchlist.length.toString().padStart(2, "0")}
                      </strong>
                    </div>
                    <button
                      aria-label="מעבר לרשימת המעקב"
                      onClick={() => navigate("watchlist")}
                    >
                      <ArrowUpLeft />
                    </button>
                  </div>
                  <div className="stat-row">
                    <span className="stat-icon">
                      <BookOpen />
                    </span>
                    <div>
                      <small>פריטים שנשמרו למחקר</small>
                      <strong>
                        {state.savedNews.length.toString().padStart(2, "0")}
                      </strong>
                    </div>
                    <button
                      aria-label="פתיחת פריטים שמורים"
                      onClick={() => {
                        navigate("news");
                        setNewsScope("saved");
                      }}
                    >
                      <ArrowUpLeft />
                    </button>
                  </div>
                </Section>
              </div>
              {feed?.version === 2 && feed.news.some(n => n.sourceId?.startsWith('sec-')) && (
                <div className="live-briefing">
                  <BriefingPanel feed={feed} />
                </div>
              )}
              <div className="section-title">
                <div>
                  <span className="eyebrow">על סדר היום</span>
                  <h2>אירועים שכדאי לבדוק</h2>
                </div>
                <button
                  className="text-button"
                  onClick={() => navigate("news")}
                >
                  לכל החדשות
                  <ArrowUpLeft size={16} />
                </button>
              </div>
              <div className="news-grid">
                {[...(feed?.news || [])].sort((a,b)=>(b.rating?.eventScore||0)-(a.rating?.eventScore||0)).slice(0, 3).map((n) => (
                  <NewsCard
                    key={n.id}
                    item={n}
                    saved={state.savedNews.some((s) => s.id === n.id)}
                    onSave={() => saveNews(n)}
                    onResearch={() => openResearch(n.ticker || n.company)}
                    read={readIds.includes(n.id)} onRead={()=>toggleRead(n.id)}
                  />
                ))}
              </div>
              {!feed?.news.length && (
                <Empty title="הפיד עדיין ריק">
                  עדכוני מחקר יופיעו כאן אחרי טעינת מקור נתונים.
                </Empty>
              )}
              <div className="home-bottom">
                <Section title="דורש תשומת לב" eyebrow="בדיקת מחקר">
                  <div className="attention-row">
                    <span className="attention-number">01</span>
                    <div>
                      <h3>אימות רשימת המעקב</h3>
                      <p>
                        {
                          state.watchlist.filter((w) =>
                            feed?.version === 2
                              ? resolveSecurity(feed, w)?.verification.status !== 'verified'
                              : !w.verified,
                          ).length
                        }{" "}
                        ניירות ממתינים לבדיקת סימול ובורסה
                      </p>
                    </div>
                    <button
                      className="icon-button"
                      aria-label="בדיקת רשימת המעקב"
                      onClick={() => navigate("watchlist")}
                    >
                      <ArrowUpLeft />
                    </button>
                  </div>
                  <div className="attention-row">
                    <span className="attention-number">02</span>
                    <div>
                      <h3>
                        {state.holdings.length
                          ? "רענון תזות ההשקעה"
                          : "הוספת האחזקה הראשונה"}
                      </h3>
                      <p>תעדו את ההנחות ואת הסיכון לפני ההחלטה הבאה</p>
                    </div>
                    <button
                      className="icon-button"
                      aria-label="בדיקת תיק ההשקעות"
                      onClick={() => navigate("portfolio")}
                    >
                      <ArrowUpLeft />
                    </button>
                  </div>
                </Section>
                <Section
                  title="רשימת המעקב"
                  eyebrow="הזדמנויות למחקר"
                  action={
                    <button
                      className="text-button"
                      onClick={() => navigate("watchlist")}
                    >
                      הכול
                      <ChevronLeft size={15} />
                    </button>
                  }
                >
                  {state.watchlist.slice(0, 4).map((w) => (
                    <button
                      className="watch-preview"
                      key={w.id}
                      onClick={() => {
                        setSelected(w.id);
                        navigate("research");
                      }}
                    >
                      <span className="company-avatar">
                        {(w.ticker || w.name).slice(0, 2)}
                      </span>
                      <span>
                        <b>{nameOf(w)}</b>
                        <small>{w.name}</small>
                      </span>
                      <span className="muted">{w.category}</span>
                      <ChevronLeft size={16} />
                    </button>
                  ))}
                </Section>
              </div>
            </>
          )}
          {tab === "portfolio" && (
            <>
              <div className="portfolio-summary">
                <div>
                  <small>הקצאה מתועדת</small>
                  <strong>
                    {allocation.toLocaleString("he-IL")}
                    <span>%</span>
                  </strong>
                </div>
                <div className="allocation-track">
                  <span style={{ width: `${allocation}%` }} />
                </div>
                <p>
                  {(100 - allocation).toLocaleString("he-IL")}% מהתיק טרם הוקצו
                  באפליקציה
                </p>
                <button
                  className="primary"
                  onClick={() => setHoldingEdit(null)}
                >
                  <Plus size={18} />
                  הוספת אחזקה
                </button>
              </div>
              <p className="muted small-note">
                האחוזים מוזנים ידנית. אין כאן מחירי שוק או חישוב תשואה.
              </p>
              {!state.holdings.length ? (
                <Empty title="כל השקעה מתחילה בתזה">
                  הוסיפו אחזקה כדי לתעד את ההקצאה, מחיר הרכישה והסיכונים.
                </Empty>
              ) : (
                <div className="holdings-grid">
                  {state.holdings.map((h) => (
                    <article className="panel holding" key={h.id}>
                      <div className="section-head">
                        <div>
                          <b dir="ltr">{h.ticker}</b>
                          <p>{h.name}</p>
                        </div>
                        <strong>{h.allocation}%</strong>
                      </div>
                      <dl>
                        <dt>מחיר רכישה ממוצע</dt>
                        <dd dir="ltr">
                          {h.averagePrice.toLocaleString()} {h.currency}
                        </dd>
                        <dt>תזת השקעה</dt>
                        <dd>{h.thesis || "טרם הוזנה"}</dd>
                        <dt>סיכונים</dt>
                        <dd>{h.risks || "טרם הוזנו"}</dd>
                      </dl>
                      <div className="form-actions">
                        <button
                          className="secondary"
                          onClick={() => setHoldingEdit(h)}
                        >
                          <Pencil size={16} />
                          עריכה
                        </button>
                        <button
                          className="text-button"
                          onClick={() => openResearch(h.ticker)}
                        >
                          מחקר
                          <ArrowUpLeft size={16} />
                        </button>
                        <button
                          className="icon-button danger"
                          aria-label={`מחיקת ${h.ticker}`}
                          onClick={() => {
                            if (confirm(`למחוק את האחזקה ${h.ticker}?`))
                              update({
                                ...state,
                                holdings: state.holdings.filter(
                                  (x) => x.id !== h.id,
                                ),
                              });
                          }}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
          {tab === "news" && (
            <>
              <div className="filters">
                <label className="search-field">
                  <Search size={18} />
                  <input
                    placeholder="חיפוש חברה, סימול או נושא…"
                    aria-label="חיפוש חדשות"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </label>
                <label className="select-field">
                  <ListFilter size={17} />
                  <select
                    aria-label="סינון לפי חשיבות"
                    value={importance}
                    onChange={(e) => setImportance(e.target.value)}
                  >
                    <option value="all">כל רמות החשיבות</option>
                    <option value="high">חשיבות גבוהה</option>
                    <option value="medium">חשיבות בינונית</option>
                    <option value="low">למעקב</option>
                  </select>
                </label>
                <select
                  aria-label="מקור הפריטים"
                  value={newsScope}
                  onChange={(e) => setNewsScope(e.target.value)}
                >
                  <option value="all">כל הפריטים</option>
                  <option value="saved">שמורים למחקר</option>
                  <option value="watchlist">המעקב שלי — סינון מקומי</option>
                  <option value="portfolio">התיק שלי — סינון מקומי</option>
                </select>
                {feed?.version===2&&<select aria-label="סינון לפי חברה" value={companyFilter} onChange={e=>setCompanyFilter(e.target.value)}><option value="all">כל החברות</option>{feed.discovery?.registry.companies.map(c=><option value={c.id} key={c.id}>{c.name}</option>)}</select>}
                {feed?.version===2&&feed.intelligence&&<select aria-label="סינון לפי תעשייה" value={industryFilter} onChange={e=>setIndustryFilter(e.target.value)}><option value="all">כל התעשיות</option>{feed.intelligence.industries.config.industries.map(i=><option value={i.id} key={i.id}>{i.name}</option>)}</select>}
                <select aria-label="חלון זמן לחדשות" value={periodFilter} onChange={e=>setPeriodFilter(e.target.value)}><option value="all">כל הזמנים</option><option value="24h">24 שעות — לפי פרסום</option></select>
                <select aria-label="מצב קריאה" value={readFilter} onChange={e=>setReadFilter(e.target.value)}><option value="all">נקרא ולא נקרא</option><option value="unread">לא נקרא</option><option value="read">נקרא</option></select>
              </div>
              <p className="muted small-note">
                {news.length} פריטים •{" "}
                {feed?.version === 2
                  ? "כותרות ומקורות ציבוריים עם סיווג לפי כללים; לא המלצת השקעה ולא ניתוח AI."
                  : "פריטי הדגמה מסומנים ואינם חדשות אמיתיות."}
              </p>
              <div className="news-grid">
                {news.map((n) => (
                  <NewsCard
                    key={n.id}
                    item={n}
                    saved={state.savedNews.some((s) => s.id === n.id)}
                    onSave={() => saveNews(n)}
                    onResearch={() => openResearch(n.ticker || n.company)}
                    read={readIds.includes(n.id)} onRead={()=>toggleRead(n.id)}
                  />
                ))}
              </div>
              {!news.length && (
                <Empty title="לא נמצאו פריטים">
                  נסו חיפוש אחר או שמרו פריטים למחקר מתוך הפיד.
                </Empty>
              )}
            </>
          )}
          {tab === "watchlist" && (
            <>
              <div className="filters">
                <label className="search-field">
                  <Search size={18} />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="חיפוש ברשימת המעקב…"
                    aria-label="חיפוש במעקב"
                  />
                </label>
                <select
                  aria-label="סינון קטגוריה"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="all">כל הקטגוריות</option>
                  {[...new Set(state.watchlist.map((s) => s.category))].map(
                    (c) => (
                      <option key={c}>{c}</option>
                    ),
                  )}
                </select>
                <button className="primary" onClick={() => setWatchEdit(null)}>
                  <Plus size={18} />
                  הוספת חברה
                </button>
              </div>
              <div className="alert">
                רשימת המעקב פרטית ואינה נשלחת לאיסוף. התאמה לרישום ציבורי דורשת
                שם חברה תואם לצורך חדשות. אימות בורסה ו־CIK נפרד מאימות זהות לחיפוש;
                רישום כפול אינו מאוחד אוטומטית.
              </div>
              <div className="watch-grid">
                {state.watchlist
                  .filter(
                    (s) =>
                      (category === "all" || s.category === category) &&
                      `${s.ticker} ${s.name}`
                        .toLowerCase()
                        .includes(query.toLowerCase()),
                  )
                  .map((s) => (
                    <article className="panel watch-card" key={s.id}>
                      <div className="section-head">
                        <span className="company-avatar">
                          {(s.ticker || s.name).slice(0, 2)}
                        </span>
                        <span className="badge">{s.category}</span>
                      </div>
                      <h3 dir="ltr">{s.ticker || s.name}</h3>
                      <p>{s.name}</p>
                      <WebNewsSearch name={s.name}/>
                      <small className="verification">
                        {feed?.version === 2
                          ? (() => {
                              const matched = resolveSecurity(feed, s);
                              const source = feed.sources.find(
                                (x) => x.securityId === matched?.id,
                              );
                              const discovery=feed.discovery?.sources.find(x=>x.securityId===matched?.id);
                              return discovery ? (discovery.status==='results' ? `חדשות ברשת • ${discovery.count} כותרות` : discovery.status==='zero-results' ? 'חיפוש הצליח — אין תוצאות' : 'חיפוש נכשל — נשמר מידע קודם') : source?.status === "ok"
                                ? `כיסוי SEC • ${matched?.exchange}`
                                : source?.url
                                  ? "מקור אינו זמין — בדקו פירוט"
                                  : "ללא כיסוי מאומת";
                            })()
                          : "סימול ובורסה טרם אומתו"}
                      </small>
                      <div className="news-actions">
                        <button
                          onClick={() => {
                            setSelected(s.id);
                            navigate("research");
                          }}
                        >
                          פתיחת מחקר
                          <ArrowUpLeft size={16} />
                        </button>
                        <button
                          aria-label={`עריכת ${s.name}`}
                          onClick={() => setWatchEdit(s)}
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          className="danger"
                          aria-label={`הסרת ${s.name}`}
                          onClick={() => {
                            if (
                              confirm(`להסיר את ${s.name} מהמעקב? המחקר יישמר.`)
                            )
                              update({
                                ...state,
                                watchlist: state.watchlist.filter(
                                  (w) => w.id !== s.id,
                                ),
                              });
                          }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </article>
                  ))}
              </div>
              {!state.watchlist.length && (
                <Empty title="הרדאר פנוי">
                  הוסיפו חברה כדי להתחיל לעקוב ולחקור.
                </Empty>
              )}
            </>
          )}
          {tab === "research" && (
            <>
              <OfficialSources ticker={security?.ticker} name={security?.name} onPrepare={setPrompt} />
              {!security ? (
                <Empty title="בחרו חברה למחקר">
                  הוסיפו חברה לתיק או לרשימת המעקב.
                </Empty>
              ) : (
                <>
                  <div className="research-toolbar">
                    <label>
                      חברה למחקר
                      <select
                        aria-label="חברה למחקר"
                        value={security.id}
                        onChange={(e) => {
                          if (dirty && !persistResearch()) return;
                          setSelected(e.target.value);
                        }}
                      >
                        {allSecurities.map((s) => (
                          <option key={s.id} value={s.id}>
                            {nameOf(s)} — {s.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <span className="muted">
                      {dirty
                        ? "שינויים שטרם נשמרו"
                        : stored
                          ? "מחקר אישי במכשיר"
                          : publicResearch
                            ? "מחקר ציבורי"
                            : "התחילו לבנות את התזה"}
                    </span>
                    <button className="primary" onClick={persistResearch}>
                      <Check size={17} />
                      שמירת מחקר
                    </button>
                    <WebNewsSearch name={security.name}/>
                  </div>
                  <ResearchExchange key={researchKey} company={(()=>{const c=officialCompany(security.ticker,security.name);return c?{id:c.id,name:c.name,label:c.label}:{id:security.id,name:security.name,label:security.ticker||security.name};})()} current={draft} onChange={next=>{setDraft(next);setDirty(true);notify("המחקר נטען לטיוטה. בדוק ושמור את המחקר.");}} onPrepare={setPrompt}/>
                  <div className="research-layout">
                    <div>
                      <div className="research-fields">
                        {Object.entries(labels).map(([key, label]) => (
                          <label
                            className={`field research-field ${key === "thesis" ? "wide" : ""}`}
                            key={key}
                          >
                            {label}
                            <textarea
                              rows={key === "thesis" ? 4 : 3}
                              value={draft[key as keyof typeof labels]}
                              placeholder={`מה חשוב לדעת על ${label}?`}
                              onChange={(e) => {
                                setDraft({ ...draft, [key]: e.target.value });
                                setDirty(true);
                              }}
                            />
                          </label>
                        ))}
                      </div>
                      <Section title="יומן מחקר">
                        <label className="field">
                          הערה חדשה
                          <textarea
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            rows={3}
                            placeholder="מה השתנה? מה עוד צריך לבדוק?"
                          />
                        </label>
                        <button
                          className="secondary"
                          disabled={!note.trim()}
                          onClick={() => {
                            const next = {
                              ...draft,
                              notes: [
                                {
                                  id: uid(),
                                  createdAt: new Date().toISOString(),
                                  text: note.trim(),
                                },
                                ...draft.notes,
                              ],
                            };
                            if (
                              update({
                                ...state,
                                research: {
                                  ...state.research,
                                  [researchKey]: next,
                                },
                              })
                            ) {
                              setDraft(next);
                              setNote("");
                              setDirty(false);
                              notify("ההערה נשמרה");
                            }
                          }}
                        >
                          <Plus size={16} />
                          הוספת הערה
                        </button>
                        {draft.notes.map((n) => (
                          <article className="note" key={n.id}>
                            <small>{dateTime(n.createdAt)}</small>
                            <p>{n.text}</p>
                          </article>
                        ))}
                        {!draft.notes.length && (
                          <p className="muted">
                            ההיסטוריה של הרעיונות שלכם תתחיל כאן.
                          </p>
                        )}
                      </Section>
                    </div>
                    <aside className="research-aside">
                      <Section title="מחשבה נוספת" eyebrow="מחקר בעזרת ChatGPT">
                        <span className="ai-mark">
                          <Activity size={27} />
                        </span>
                        <p>
                          הפכו את התזה, ההערות והמקורות לבקשת ניתוח מסודרת
                          בעברית.
                        </p>
                        <button
                          className="primary"
                          onClick={() =>
                            setPrompt(
                              buildPrompt(
                                security.name,
                                security.ticker,
                                draft,
                                related,
                                publicResearch?.sourceUrls,
                                officialCompany(security.ticker,security.name)?.id || security.id,
                              ),
                            )
                          }
                        >
                          הכנת בקשת ניתוח
                          <ArrowUpLeft size={17} />
                        </button>
                        <small>
                          המידע אינו מועבר אוטומטית. העתיקו והדביקו אותו
                          ב־ChatGPT לפי בחירתכם.
                        </small>
                      </Section>
                      <Section title="מקורות ופריטים">
                        <p className="muted">
                          {related.length} פריטים רלוונטיים
                        </p>
                        {related.map((n) => (
                          <a
                            className="source-item"
                            href={n.sourceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            key={n.id}
                          >
                            {n.demo && <small>הדגמה בלבד</small>}
                            {n.headline}
                            <ExternalLink size={14} />
                          </a>
                        ))}
                        {publicResearch?.sourceUrls.map((url) => (
                          <a
                            key={url}
                            className="source-item"
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {new URL(url).hostname}
                            <ExternalLink size={14} />
                          </a>
                        ))}
                        {!related.length &&
                          !publicResearch?.sourceUrls.length && (
                            <p>טרם נוספו מקורות לחברה זו.</p>
                          )}
                      </Section>
                    </aside>
                  </div>
                </>
              )}
            </>
          )}
          <footer className="main-footer">
            <span dir="ltr">
              PULSE <span>•</span> A CLEARER PERSPECTIVE
            </span>
            <small>סביבת מחקר אישית • אינה ייעוץ השקעות</small>
          </footer>
        </main>
      </div>
      <nav className="bottom-nav" aria-label="ניווט נייד">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => navigate(t.id)}
            aria-current={tab === t.id ? "page" : undefined}
            className={tab === t.id ? "active" : ""}
          >
            <t.icon size={22} />
            <span>{t.label}</span>
          </button>
        ))}
      </nav>
      {toast && (
        <div className="toast" role="status">
          <Check size={18} />
          {toast}
        </div>
      )}
      {holdingEdit !== undefined && (
        <HoldingForm
          holding={holdingEdit}
          remaining={100 - allocation + (holdingEdit?.allocation || 0)}
          close={() => setHoldingEdit(undefined)}
          save={(h) => {
            if (
              state.holdings.some((x) => x.ticker === h.ticker && x.id !== h.id)
            ) {
              notify("הסימול כבר קיים בתיק");
              return;
            }
            if (
              update({
                ...state,
                holdings: holdingEdit
                  ? state.holdings.map((x) => (x.id === h.id ? h : x))
                  : [...state.holdings, h],
              })
            ) {
              setHoldingEdit(undefined);
              notify("האחזקה נשמרה במכשיר");
            }
          }}
        />
      )}
      {watchEdit !== undefined && (
        <WatchForm
          security={watchEdit}
          close={() => setWatchEdit(undefined)}
          save={(s) => {
            if (
              state.watchlist.some(
                (w) =>
                  w.id !== s.id &&
                  ((s.ticker && w.ticker === s.ticker) ||
                    w.name.toLowerCase() === s.name.toLowerCase()),
              )
            ) {
              notify("החברה כבר ברשימת המעקב");
              return;
            }
            if (
              update({
                ...state,
                watchlist: watchEdit
                  ? state.watchlist.map((w) => (w.id === s.id ? s : w))
                  : [...state.watchlist, s],
              })
            ) {
              setWatchEdit(undefined);
              notify("רשימת המעקב עודכנה");
            }
          }}
        />
      )}
      {prompt !== null && (
        <Modal title="בקשת ניתוח ל־ChatGPT" close={() => setPrompt(null)}>
          <p className="muted">
            בדקו את התוכן. העתיקו אותו, פתחו את ChatGPT והדביקו בשיחה. נתוני
            התיק אינם מועברים אוטומטית.
          </p>
          <label className="field">
            טקסט להעתקה
            <textarea
              className="prompt-text"
              rows={14}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </label>
          <div className="form-actions">
            <button
              className="primary"
              onClick={async () =>
                notify(
                  (await copyText(prompt))
                    ? "הבקשה הועתקה. כעת ניתן להדביק ב־ChatGPT."
                    : "ההעתקה נחסמה. סמנו את הטקסט והעתיקו ידנית.",
                )
              }
            >
              <Copy size={17} />
              העתקת הבקשה
            </button>
            <a
              className="secondary"
              href="https://chatgpt.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              פתיחת ChatGPT
              <ExternalLink size={16} />
            </a>
          </div>
        </Modal>
      )}
      {help && (
        <Modal title="PULSE על מסך הבית" close={() => setHelp(false)}>
          <p>
            באייפון: פתחו את האתר ב־Safari, הקישו על שיתוף ובחרו ״הוספה למסך
            הבית״.
          </p>
          <p>
            באנדרואיד: פתחו ב־Chrome ובחרו ״התקנת אפליקציה״ או ״הוספה למסך הבית״
            בתפריט.
          </p>
          {install && (
            <button
              className="primary"
              onClick={async () => {
                await install.prompt();
                await install.userChoice;
                setInstall(null);
              }}
            >
              <Download size={17} />
              התקנת PULSE
            </button>
          )}
          <p className="muted">
            התקנה דורשת אתר בפריסת HTTPS. לאחר הביקור הראשון האפליקציה זמינה גם
            ללא רשת. המידע האישי נשמר רק בדפדפן הזה; ייצאו גיבוי לפני החלפת
            מכשיר או ניקוי נתונים.
          </p>
          <button className="secondary" onClick={exportData}>
            <Download size={17} />
            ייצוא גיבוי אישי
          </button>
        </Modal>
      )}
    </div>
  );
}

function HoldingForm({
  holding,
  remaining,
  close,
  save,
}: {
  holding: Holding | null;
  remaining: number;
  close: () => void;
  save: (h: Holding) => void;
}) {
  const [h, setH] = useState<Holding>(
    holding || {
      id: uid(),
      ticker: "",
      name: "",
      allocation: 0,
      averagePrice: 0,
      currency: "USD",
      thesis: "",
      risks: "",
    },
  );
  return (
    <Modal title={holding ? "עריכת אחזקה" : "הוספת אחזקה"} close={close}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save({
            ...h,
            ticker: h.ticker.trim().toUpperCase(),
            name: h.name.trim(),
            allocation: Number(h.allocation),
            averagePrice: Number(h.averagePrice),
          });
        }}
      >
        <div className="form-grid">
          <label className="field">
            סימול
            <input
              required
              maxLength={30}
              value={h.ticker}
              onChange={(e) => setH({ ...h, ticker: e.target.value })}
              dir="ltr"
            />
          </label>
          <label className="field">
            שם החברה
            <input
              required
              maxLength={120}
              value={h.name}
              onChange={(e) => setH({ ...h, name: e.target.value })}
            />
          </label>
          <label className="field">
            הקצאה באחוזים (עד {remaining.toFixed(2)}%)
            <input
              type="number"
              required
              min="0"
              max={remaining}
              step="any"
              value={h.allocation}
              onChange={(e) =>
                setH({ ...h, allocation: e.target.valueAsNumber })
              }
            />
          </label>
          <label className="field">
            מחיר רכישה ממוצע
            <input
              type="number"
              required
              min="0"
              step="any"
              value={h.averagePrice}
              onChange={(e) =>
                setH({ ...h, averagePrice: e.target.valueAsNumber })
              }
            />
          </label>
          <label className="field">
            מטבע
            <select
              value={h.currency}
              onChange={(e) => setH({ ...h, currency: e.target.value })}
            >
              {["USD", "ILS", "EUR", "GBP"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          תזת השקעה
          <textarea
            rows={3}
            value={h.thesis}
            onChange={(e) => setH({ ...h, thesis: e.target.value })}
          />
        </label>
        <label className="field">
          הערות סיכון
          <textarea
            rows={3}
            value={h.risks}
            onChange={(e) => setH({ ...h, risks: e.target.value })}
          />
        </label>
        <div className="form-actions">
          <button className="primary" type="submit">
            שמירת אחזקה
          </button>
          <button type="button" className="secondary" onClick={close}>
            ביטול
          </button>
        </div>
      </form>
    </Modal>
  );
}
function WatchForm({
  security,
  close,
  save,
}: {
  security: Security | null;
  close: () => void;
  save: (s: Security) => void;
}) {
  const [s, setS] = useState<Security>(
    security || {
      id: uid(),
      name: "",
      ticker: "",
      category: "כללי",
      verified: false,
    },
  );
  return (
    <Modal title={security ? "עריכת חברה" : "הוספה לרשימת המעקב"} close={close}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save({
            ...s,
            name: s.name.trim(),
            ticker: s.ticker.trim().toUpperCase(),
            category: s.category.trim(),
            verified: false,
          });
        }}
      >
        <label className="field">
          שם החברה
          <input
            required
            maxLength={120}
            value={s.name}
            onChange={(e) => setS({ ...s, name: e.target.value })}
          />
        </label>
        <label className="field">
          סימול מוצע (אופציונלי)
          <input
            maxLength={30}
            dir="ltr"
            value={s.ticker}
            onChange={(e) => setS({ ...s, ticker: e.target.value })}
          />
        </label>
        <label className="field">
          קטגוריה
          <input
            required
            maxLength={60}
            value={s.category}
            onChange={(e) => setS({ ...s, category: e.target.value })}
          />
        </label>
        <p className="muted">
          הסימול יישמר כלא מאומת. חיבור לנתונים ידרוש אימות סימול ובורסה בשלב
          הבא.
        </p>
        <div className="form-actions">
          <button type="submit" className="primary">
            שמירת חברה
          </button>
          <button className="secondary" type="button" onClick={close}>
            ביטול
          </button>
        </div>
      </form>
    </Modal>
  );
}
