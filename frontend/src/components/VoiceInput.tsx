import { useRef, useState } from "react";
import { useT } from "../i18n";
import { loadWhisper, micSupported, transcribe, whisperDownloaded } from "../lib/speech";

type Status = "idle" | "loading" | "recording" | "transcribing" | "denied" | "error";

/** Push-to-talk dictation. First use downloads the speech model (needs signal); after that it works offline. */
export function VoiceInput({ lang, online, onText }: { lang: string; online: boolean; onText: (text: string) => void }) {
  const t = useT();
  const [status, setStatus] = useState<Status>("idle");
  const [pct, setPct] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  if (!micSupported()) return null;

  async function start() {
    try {
      if (!whisperDownloaded()) {
        setStatus("loading");
        await loadWhisper((f) => setPct(Math.round(f * 100)));
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunks.current = [];
      rec.ondataavailable = (e) => chunks.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        setStatus("transcribing");
        try {
          const text = await transcribe(new Blob(chunks.current, { type: rec.mimeType }), lang);
          if (text) onText(text);
          setStatus("idle");
        } catch {
          setStatus("error");
        }
      };
      recorder.current = rec;
      rec.start();
      setStatus("recording");
    } catch (err) {
      setStatus(err instanceof DOMException && err.name === "NotAllowedError" ? "denied" : "error");
    }
  }

  function stop() {
    recorder.current?.stop();
  }

  const busy = status === "loading" || status === "transcribing";
  const label =
    status === "recording"
      ? t("mic_stop")
      : status === "loading"
        ? t("mic_loading", { pct })
        : status === "transcribing"
          ? t("mic_transcribing")
          : t("mic_start");

  return (
    <div className="row" style={{ marginTop: 8, alignItems: "center" }}>
      <button
        type="button"
        className="secondary"
        onClick={status === "recording" ? stop : start}
        disabled={busy || (!online && !whisperDownloaded())}
        aria-pressed={status === "recording"}
      >
        {status === "recording" ? "⏹ " : "🎤 "}
        {label}
      </button>
      {status === "denied" && <span className="muted">{t("mic_denied")}</span>}
      {status === "error" && <span className="muted">{t("error")}</span>}
    </div>
  );
}
