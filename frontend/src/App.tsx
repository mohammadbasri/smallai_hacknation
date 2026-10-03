import { useState } from "react";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import { OnlineBadge } from "./components/OnlineBadge";
import { LangContext, loadLang, saveLang, useT, type Lang } from "./i18n";
import { Home } from "./pages/Home";

function Shell() {
  const t = useT();
  return (
    <div className="app">
      <header>
        <h1>{t("app_title")}</h1>
        <div className="row" style={{ flex: "0 0 auto", alignItems: "center" }}>
          <OnlineBadge />
          <LanguageSwitcher />
        </div>
      </header>
      <Home />
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
