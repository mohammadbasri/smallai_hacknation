import { useState, type FormEvent } from "react";
import { useT } from "../i18n";
import { copyText } from "../lib/clipboard";
import { listingText, type Hub } from "../lib/models";
import { saveProfile, useStore, type Profile } from "../lib/store";

const FIELDS: (keyof Profile)[] = [
  "farm_name", "operator_name", "village", "phone", "languages", "price_adult", "price_child", "currency", "duration",
  "includes", "open_days", "start_times", "location_hint", "directions_hint", "dietary_note", "max_party",
];
const LONG: (keyof Profile)[] = ["includes", "location_hint", "directions_hint", "dietary_note", "languages"];

export function Listing({ hub }: { hub: Hub }) {
  const t = useT();
  const { profile } = useStore();
  const [draft, setDraft] = useState<Profile>(profile);
  const [lang, setLang] = useState<"en" | "fr" | "sw">("en");
  const [notice, setNotice] = useState<string | null>(null);

  function submit(e: FormEvent) {
    e.preventDefault();
    saveProfile(draft);
    setNotice(t("profile_saved"));
  }

  const text = listingText(hub, lang, profile);

  return (
    <>
      <form className="card" onSubmit={submit}>
        <h2>{t("listing_title")}</h2>
        <p className="muted">{t("listing_help")}</p>
        <div className="grid2">
          {FIELDS.map((f) => (
            <div key={f} className={LONG.includes(f) ? "span2" : ""}>
              <label htmlFor={`p-${f}`}>{t(f as "farm_name")}</label>
              {LONG.includes(f) ? (
                <textarea id={`p-${f}`} value={String(draft[f])} onChange={(e) => setDraft({ ...draft, [f]: e.target.value })} style={{ minHeight: 56 }} />
              ) : (
                <input
                  id={`p-${f}`}
                  type={f === "max_party" ? "number" : "text"}
                  value={String(draft[f])}
                  onChange={(e) => setDraft({ ...draft, [f]: f === "max_party" ? Number(e.target.value) : e.target.value })}
                />
              )}
            </div>
          ))}
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button type="submit">{t("save_profile")}</button>
        </div>
        {notice && <p className="notice-inline">{notice}</p>}
      </form>

      <section className="card">
        <div className="row" style={{ alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>{t("listing_text")}</h2>
          <select value={lang} onChange={(e) => setLang(e.target.value as "en" | "fr" | "sw")} style={{ width: "auto", flex: "0 0 auto" }}>
            <option value="en">English</option>
            <option value="fr">Français</option>
            <option value="sw">Kiswahili</option>
          </select>
        </div>
        <pre className="listing">{text}</pre>
        <button type="button" className="secondary" onClick={() => copyText(text).then((ok) => setNotice(ok ? t("copied") : t("error")))}>
          {t("copy")}
        </button>
      </section>
    </>
  );
}
