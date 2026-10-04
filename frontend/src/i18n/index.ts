/** Tiny dependency-free i18n for the OPERATOR side (Noor). Kiswahili is the demo language, English the fallback.
 *  Visitor-facing text is not here: it lives in shared/templates/replies.json (en/fr/sw). */
import { createContext, useContext } from "react";
import en from "./en.json";
import sw from "./sw.json";

export type Lang = "en" | "sw";
export type Dict = typeof en;

export const DICTS: Record<Lang, Dict> = { en, sw };
export const LANG_NAMES: Record<Lang, string> = { en: "English", sw: "Kiswahili" };

export const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({
  lang: "sw",
  setLang: () => {},
});

export function useLang(): Lang {
  return useContext(LangContext).lang;
}

export function useT() {
  const { lang } = useContext(LangContext);
  const dict = DICTS[lang];
  return (key: keyof Dict, vars?: Record<string, string | number>) => {
    let s: string = dict[key] ?? en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
    return s;
  };
}

export function loadLang(): Lang {
  try {
    const saved = localStorage.getItem("karibu.lang");
    if (saved === "en" || saved === "sw") return saved;
  } catch {
    /* storage unavailable */
  }
  return "sw";
}

export function saveLang(l: Lang) {
  try {
    localStorage.setItem("karibu.lang", l);
  } catch {
    /* ignore */
  }
}
