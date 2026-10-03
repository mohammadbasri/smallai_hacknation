import { useContext } from "react";
import { LANG_NAMES, LangContext, useT, type Lang } from "../i18n";

export function LanguageSwitcher() {
  const { lang, setLang } = useContext(LangContext);
  const t = useT();
  return (
    <select aria-label={t("language")} value={lang} onChange={(e) => setLang(e.target.value as Lang)} style={{ width: "auto" }}>
      {(Object.keys(LANG_NAMES) as Lang[]).map((l) => (
        <option key={l} value={l}>
          {LANG_NAMES[l]}
        </option>
      ))}
    </select>
  );
}
