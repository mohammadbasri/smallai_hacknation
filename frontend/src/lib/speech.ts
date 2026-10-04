/** Offline voice: Whisper (transformers.js) for speech-to-text, the browser's speechSynthesis for text-to-speech.
 *  Whisper weights download once (~250 MB) and are cached. speechSynthesis works offline only if the device
 *  has a local voice for the language (common on Android for Hindi/English). */

const WHISPER_ID = "onnx-community/whisper-small";
const WHISPER_KEY = "smallai.whisper_ready";
const WHISPER_LANG: Record<string, string> = { hi: "hindi", en: "english" };
const VOICE_LANG: Record<string, string> = { hi: "hi-IN", en: "en-IN" };

type Transcriber = (audio: Float32Array, opts: Record<string, unknown>) => Promise<{ text: string }>;

let transcriber: Transcriber | null = null;
let loading: Promise<void> | null = null;

export function micSupported(): boolean {
  return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
}

export function whisperDownloaded(): boolean {
  try {
    return localStorage.getItem(WHISPER_KEY) === WHISPER_ID;
  } catch {
    return false;
  }
}

export async function loadWhisper(onProgress?: (fraction: number) => void): Promise<void> {
  if (transcriber) return;
  loading ??= (async () => {
    const { pipeline } = await import("@huggingface/transformers");
    const files = new Map<string, { loaded: number; total: number }>();
    const pipe = await pipeline("automatic-speech-recognition", WHISPER_ID, {
      dtype: "q8",
      progress_callback: (e: { status: string; file?: string; loaded?: number; total?: number }) => {
        if (e.status !== "progress" || !e.file) return;
        files.set(e.file, { loaded: e.loaded ?? 0, total: e.total ?? 0 });
        let loaded = 0;
        let total = 0;
        files.forEach((f) => {
          loaded += f.loaded;
          total += f.total;
        });
        if (total > 0) onProgress?.(loaded / total);
      },
    });
    transcriber = pipe as unknown as Transcriber;
    try {
      localStorage.setItem(WHISPER_KEY, WHISPER_ID);
    } catch {
      /* ignore */
    }
  })().finally(() => {
    loading = null;
  });
  await loading;
}

async function toMono16k(blob: Blob): Promise<Float32Array> {
  const ctx = new AudioContext({ sampleRate: 16000 });
  try {
    const audio = await ctx.decodeAudioData(await blob.arrayBuffer());
    return audio.getChannelData(0);
  } finally {
    void ctx.close();
  }
}

export async function transcribe(blob: Blob, lang: string): Promise<string> {
  await loadWhisper();
  const audio = await toMono16k(blob);
  const out = await transcriber!(audio, {
    language: WHISPER_LANG[lang] ?? "english",
    task: "transcribe",
    chunk_length_s: 30,
  });
  return out.text.trim();
}

export function ttsSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function voiceFor(tag: string): SpeechSynthesisVoice | undefined {
  const base = tag.split("-")[0];
  const voices = window.speechSynthesis.getVoices();
  return voices.find((v) => v.lang === tag) ?? voices.find((v) => v.lang.startsWith(base));
}

/** True if the device has a voice for this UI language (voices may load a moment after page load). */
export function hasVoice(lang: string): boolean {
  return ttsSupported() && !!voiceFor(VOICE_LANG[lang] ?? "en-IN");
}

/** Reads text aloud line by line, picking Hindi or English per line by script, so mixed answers sound right. */
export function speak(text: string, onEnd?: () => void): void {
  if (!ttsSupported()) return;
  window.speechSynthesis.cancel();
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  lines.forEach((line, i) => {
    const u = new SpeechSynthesisUtterance(line);
    const tag = /[ऀ-ॿ]/.test(line) ? "hi-IN" : "en-IN";
    u.lang = tag;
    const v = voiceFor(tag);
    if (v) u.voice = v;
    if (i === lines.length - 1) {
      u.onend = () => onEnd?.();
      u.onerror = () => onEnd?.();
    }
    window.speechSynthesis.speak(u);
  });
}

export function stopSpeaking(): void {
  if (ttsSupported()) window.speechSynthesis.cancel();
}
