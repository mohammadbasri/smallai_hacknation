/** Tiny dependency-free i18n. Add a language by adding a JSON file and registering it here.
 *  The brief requires at least one interaction in a named local language. Hindi (hi). */
import { createContext, useContext } from "react";
import en from "./en.json";
import hi from "./hi.json";

export type Lang = "en" | "hi";
export type Dict = typeof en;

export const DICTS: Record<Lang, Dict> = { en, hi };
export const LANG_NAMES: Record<Lang, string> = { en: "English", hi: "हिन्दी" };

export const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({
  lang: "hi",
  setLang: () => {},
});

export function useT() {
  const { lang } = useContext(LangContext);
  const dict = DICTS[lang];
  return (key: keyof Dict, vars?: Record<string, string | number>) => {
    let s: string = dict[key] ?? en[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
    return s;
  };
}

export function loadLang(): Lang {
  try {
    const saved = localStorage.getItem("lang");
    if (saved === "en" || saved === "hi") return saved;
  } catch {
    /* storage unavailable */
  }
  return "hi";
}

export function saveLang(l: Lang) {
  try {
    localStorage.setItem("lang", l);
  } catch {
    /* ignore */
  }
}
