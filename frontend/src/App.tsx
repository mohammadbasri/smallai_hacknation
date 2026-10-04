import { useCallback, useEffect, useState } from "react";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import { Nav, type Page } from "./components/Nav";
import { OnlineBadge } from "./components/OnlineBadge";
import { useOnline } from "./hooks/useOnline";
import { LangContext, loadLang, saveLang, useT, type Lang } from "./i18n";
import { loadHub, type Hub } from "./lib/models";
import { flush, pending } from "./lib/offlineQueue";
import { useStore, type Enquiry } from "./lib/store";
import { About } from "./pages/About";
import { Bookings } from "./pages/Bookings";
import { Feedback } from "./pages/Feedback";
import { Inbox } from "./pages/Inbox";
import { Listing } from "./pages/Listing";
import { Sms } from "./pages/Sms";

function Shell() {
  const t = useT();
  const online = useOnline();
  const { enquiries } = useStore();
  const [page, setPage] = useState<Page>("inbox");
  const [hub, setHub] = useState<Hub | null>(null);
  const [hubError, setHubError] = useState(false);
  const [prefill, setPrefill] = useState<Enquiry | null>(null);
  const [queued, setQueued] = useState(pending().length);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  useEffect(() => {
    loadHub()
      .then(setHub)
      .catch(() => setHubError(true));
  }, []);

  // Store-and-forward: whenever we are online and something is queued, try to send it.
  const trySync = useCallback(async () => {
    if (!online || pending().length === 0) return;
    try {
      const n = await flush();
      if (n > 0) setSyncNote(t("synced", { n }));
    } catch {
      /* still offline in practice: keep queued */
    }
    setQueued(pending().length);
  }, [online, t]);

  useEffect(() => {
    trySync();
    const id = window.setInterval(() => {
      setQueued(pending().length);
      trySync();
    }, 15000);
    return () => window.clearInterval(id);
  }, [trySync, enquiries.length]);

  const waiting = enquiries.filter((e) => e.status === "new").length;

  return (
    <div className="app">
      <header>
        <div>
          <h1>{t("app_title")}</h1>
          <div className="muted small">{t("app_subtitle")}</div>
        </div>
        <div className="toolbar">
          <OnlineBadge />
          <LanguageSwitcher />
        </div>
      </header>

      {!hub && !hubError && <div className="card muted">{t("loading_models")}</div>}
      {hubError && <div className="card result-ask">{t("models_failed")}</div>}
      {hub && page === "inbox" && (
        <Inbox
          hub={hub}
          onCreateBooking={(e) => {
            setPrefill(e);
            setPage("bookings");
          }}
        />
      )}
      {hub && page === "bookings" && <Bookings hub={hub} prefill={prefill} onPrefillUsed={() => setPrefill(null)} />}
      {hub && page === "feedback" && <Feedback hub={hub} />}
      {hub && page === "listing" && <Listing hub={hub} />}
      {page === "sms" && <Sms />}
      {hub && page === "about" && <About hub={hub} />}

      {(queued > 0 || syncNote) && (
        <div className="card">
          <div className="row" style={{ alignItems: "center" }}>
            <span className="muted">{queued > 0 ? t("queued", { n: queued }) : syncNote}</span>
            {queued > 0 && (
              <button type="button" className="secondary" onClick={trySync} disabled={!online}>
                {t("sync_now")}
              </button>
            )}
          </div>
        </div>
      )}
      {hub && <p className="muted small center">{t("models_ready", { kb: Math.round(hub.totalBytes / 1024) })}</p>}

      <Nav page={page} onChange={setPage} badge={{ inbox: waiting }} />
    </div>
  );
}

export default function App() {
  const [lang, setLangState] = useState<Lang>(loadLang);
  const setLang = (l: Lang) => {
    setLangState(l);
    saveLang(l);
    document.documentElement.lang = l;
  };
  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <Shell />
    </LangContext.Provider>
  );
}
