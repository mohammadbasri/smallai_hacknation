import { useEffect, useState } from "react";
import { useT } from "../i18n";
import { llmDownloaded, llmReady, llmSupported, loadLLM } from "../lib/llm";

type Status = "idle" | "loading" | "ready" | "error";

/** Download-once button for the on-device model. Auto-loads from cache when it was downloaded before. */
export function OfflineModel({ online, onReady }: { online: boolean; onReady: () => void }) {
  const t = useT();
  const [status, setStatus] = useState<Status>(llmReady() ? "ready" : "idle");
  const [pct, setPct] = useState(0);

  async function start() {
    setStatus("loading");
    try {
      await loadLLM((f) => setPct(Math.round(f * 100)));
      setStatus("ready");
      onReady();
    } catch {
      setStatus("error");
    }
  }

  useEffect(() => {
    if (status === "idle" && llmSupported() && llmDownloaded()) void start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!llmSupported()) return <p className="muted">{t("model_unsupported")}</p>;
  if (status === "ready") return <p className="muted">{t("model_ready")}</p>;
  if (status === "loading") {
    return (
      <div className="card">
        <div className="muted">{t("model_downloading", { pct })}</div>
        <div className="meter" aria-hidden="true">
          <div style={{ width: `${pct}%` }} />
        </div>
      </div>
    );
  }
  return (
    <div className="card">
      <p className="muted" style={{ marginTop: 0 }}>
        {status === "error" ? t("error") : t("model_prompt")}
      </p>
      <button type="button" className="secondary" onClick={start} disabled={!online && !llmDownloaded()}>
        {t("model_download")}
      </button>
    </div>
  );
}
