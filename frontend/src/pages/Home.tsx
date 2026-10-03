import { useContext, useEffect, useState, type FormEvent } from "react";
import { api, type InferenceResponse, type Sector } from "../api/client";
import { ResultCard } from "../components/ResultCard";
import { SectorPicker } from "../components/SectorPicker";
import { useOnline } from "../hooks/useOnline";
import { LangContext, useT } from "../i18n";
import { enqueue, flush, getClientId, pending } from "../lib/offlineQueue";

export function Home() {
  const t = useT();
  const { lang } = useContext(LangContext);
  const online = useOnline();

  const [sector, setSector] = useState<Sector>("agriculture");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<InferenceResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [queued, setQueued] = useState(pending().length);

  // When signal returns, forward whatever was saved on the phone.
  useEffect(() => {
    if (!online || queued === 0) return;
    flush()
      .then(() => setQueued(pending().length))
      .catch(() => {});
  }, [online, queued]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    setNotice(null);
    setResult(null);
    try {
      // TODO: for the hackathon, run the small model ON DEVICE here (ONNX Runtime Web / TF.js / WebLLM)
      // and only call the API for sync. The server call below is the boilerplate placeholder.
      const res = await api.infer({ sector, text, language: lang, client_id: getClientId() });
      setResult(res);
      enqueue(sector, { text, decision: res.decision, label: res.label, confidence: res.confidence }, lang);
      setQueued(pending().length);
    } catch {
      enqueue(sector, { text }, lang);
      setQueued(pending().length);
      setNotice(online ? t("error") : t("saved_offline"));
    } finally {
      setBusy(false);
    }
  }

  async function onSyncNow() {
    try {
      await flush();
    } catch {
      setNotice(t("error"));
    }
    setQueued(pending().length);
  }

  return (
    <>
      <form className="card" onSubmit={onSubmit}>
        <SectorPicker value={sector} onChange={setSector} />
        <div style={{ marginTop: 16 }}>
          <label htmlFor="input">{t("input_label")}</label>
          <textarea id="input" value={text} onChange={(e) => setText(e.target.value)} placeholder={t("input_placeholder")} />
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button type="submit" disabled={busy || !text.trim()}>
            {busy ? t("checking") : t("submit")}
          </button>
        </div>
      </form>

      {notice && <div className="card result-ask">{notice}</div>}
      {result && <ResultCard result={result} />}

      {queued > 0 && (
        <div className="card">
          <div className="row" style={{ alignItems: "center" }}>
            <span className="muted">{t("queued", { n: queued })}</span>
            <button type="button" className="secondary" onClick={onSyncNow} disabled={!online}>
              {t("sync_now")}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
