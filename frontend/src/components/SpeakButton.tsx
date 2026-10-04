import { useEffect, useState } from "react";
import { useT } from "../i18n";
import { hasVoice, speak, stopSpeaking, ttsSupported } from "../lib/speech";

/** Reads the answer aloud. Hidden when the device has no voice for the language. */
export function SpeakButton({ text, lang }: { text: string; lang: string }) {
  const t = useT();
  const [playing, setPlaying] = useState(false);
  const [available, setAvailable] = useState(() => hasVoice(lang));

  useEffect(() => {
    setAvailable(hasVoice(lang));
    if (!ttsSupported()) return;
    const update = () => setAvailable(hasVoice(lang));
    window.speechSynthesis.addEventListener("voiceschanged", update);
    return () => {
      window.speechSynthesis.removeEventListener("voiceschanged", update);
      stopSpeaking();
    };
  }, [lang]);

  if (!available) return <p className="muted">{t("no_voice")}</p>;
  return (
    <button
      type="button"
      className="secondary"
      onClick={() => {
        if (playing) {
          stopSpeaking();
          setPlaying(false);
        } else {
          setPlaying(true);
          speak(text, () => setPlaying(false));
        }
      }}
    >
      {playing ? "⏹ " : "🔊 "}
      {playing ? t("speak_stop") : t("speak")}
    </button>
  );
}
