/** On-device Cohere Tiny Aya via transformers.js (ONNX + WebGPU). Weights download once, are cached by the
 *  browser, then work offline. The model writes the answer and replies UNSURE to defer to a person.
 *  Note: Tiny Aya weights are CC-BY-NC 4.0 (non-commercial). */
import type { InferenceResponse, Sector } from "../api/client";

// "fire" is the South Asia-tuned variant (Hindi, Bengali, Marathi, Tamil...). Others: global, earth, water.
export const MODEL_ID = "onnx-community/tiny-aya-fire-ONNX";

const SOURCES = "Cohere Tiny Aya running on this device";
const READY_KEY = "smallai.llm_ready";

type Generator = (messages: unknown, opts: Record<string, unknown>) => Promise<{ generated_text: { content: string }[] }[]>;

let generator: Generator | null = null;
let loading: Promise<void> | null = null;

export function llmSupported(): boolean {
  return typeof navigator !== "undefined" && "gpu" in navigator;
}

/** True once the weights were downloaded on this device (they may still need loading into memory). */
export function llmDownloaded(): boolean {
  try {
    return localStorage.getItem(READY_KEY) === MODEL_ID;
  } catch {
    return false;
  }
}

export function llmReady(): boolean {
  return generator !== null;
}

async function build(dtype: "q4f16" | "q4", onProgress?: (fraction: number) => void): Promise<Generator> {
  const { pipeline } = await import("@huggingface/transformers");
  const files = new Map<string, { loaded: number; total: number }>();
  const pipe = await pipeline("text-generation", MODEL_ID, {
    device: "webgpu",
    dtype,
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
  return pipe as unknown as Generator;
}

export async function loadLLM(onProgress?: (fraction: number) => void): Promise<void> {
  if (generator) return;
  loading ??= (async () => {
    try {
      generator = await build("q4f16", onProgress);
    } catch {
      generator = await build("q4", onProgress); // GPUs without shader-f16
    }
    try {
      localStorage.setItem(READY_KEY, MODEL_ID);
    } catch {
      /* ignore */
    }
  })().finally(() => {
    loading = null;
  });
  await loading;
}

const LANGS: Record<string, { name: string; wants: string; reply: string; check: string; shot: [string, string] }> = {
  en: {
    name: "English",
    wants: "Visitor wants",
    reply: "Suggested reply",
    check: "Check before sending",
    shot: [
      "Hello, 4 of us would like to visit your village next Saturday. How much for a guided walk?",
      "Visitor wants: A guided village walk next Saturday for 4 people, and the price.\n" +
        "Suggested reply: Hello, thank you for writing! A guided walk for 4 people next Saturday is possible. The price is [price] per person. Please tell us what time suits you.\n" +
        "Check before sending: Are you free next Saturday? Fill in the price.",
    ],
  },
  hi: {
    name: "Hindi (Devanagari script)",
    wants: "आगंतुक क्या चाहता है",
    reply: "सुझाया गया जवाब",
    check: "भेजने से पहले जाँचें",
    shot: [
      "Hello, we are 4 people. Can we visit your village next Saturday? How much for a guided walk?",
      "आगंतुक क्या चाहता है: अगले शनिवार 4 लोगों के लिए गाँव की गाइडेड वॉक और उसकी कीमत।\n" +
        "सुझाया गया जवाब: Hello, thank you for your message! A guided walk for 4 people next Saturday is possible. The price is [price] per person. Please tell us what time suits you.\n" +
        "भेजने से पहले जाँचें: क्या आप अगले शनिवार खाली हैं? कीमत भरें।",
    ],
  },
};

function systemPrompt(sector: Sector, l: (typeof LANGS)[string]): string {
  return (
    `You are an assistant to a small, family-run ${sector} operator in rural India (a homestay, local guide or village tour with only a few visitors a month). ` +
    `The operator has a basic phone, unreliable internet, and may not share a language with visitors. ` +
    `Your job: help with ONE visitor enquiry or situation, so the operator can understand it and respond well.\n\n` +
    `Rules:\n` +
    `- You only inform. The operator decides and sends the reply. Never say a booking is confirmed.\n` +
    `- Never invent prices, dates, availability, opening times, distances, safety claims, phone numbers or local facts. ` +
    `Where a fact is needed, write a placeholder in square brackets such as [price] or [date] for the operator to fill in.\n` +
    `- Use warm, simple words and short sentences.\n` +
    `- If the message is not about a visitor enquiry, booking, directions, experience or feedback, or it is unclear, or you would have to guess, reply with exactly: UNSURE\n\n` +
    `Reply in ${l.name} using exactly these three lines and nothing else:\n` +
    `${l.wants}: one sentence.\n` +
    `${l.reply}: 2-3 short sentences, written in the language the visitor used (if unclear, in ${l.name}).\n` +
    `${l.check}: at most 2 items the operator must verify or fill in.`
  );
}

export async function askLocal(sector: Sector, text: string, language: string): Promise<InferenceResponse> {
  if (!generator) throw new Error("LLM not loaded");
  const l = LANGS[language] ?? LANGS.en;

  const out = await generator(
    [
      { role: "system", content: systemPrompt(sector, l) },
      { role: "user", content: l.shot[0] },
      { role: "assistant", content: l.shot[1] },
      { role: "user", content: text },
    ],
    { max_new_tokens: 320, do_sample: false, repetition_penalty: 1.05 }
  );

  const turns = out[0].generated_text;
  const answer = (turns[turns.length - 1]?.content ?? "").trim();
  const unsure = answer === "" || answer.toUpperCase().startsWith("UNSURE");

  return {
    decision: unsure ? "ask_a_person" : "answer",
    label: null,
    confidence: 0, // generation gives no calibrated score; the UI hides the meter when 0
    explanation: unsure
      ? language === "hi"
        ? "पक्का नहीं है। कृपया किसी व्यक्ति (टूर गाइड या पर्यटन अधिकारी) से पूछें।"
        : "Not sure. Please ask a person (a tour guide or tourism officer)."
      : answer,
    language,
    model_name: "tiny-aya-fire",
    model_version: "on-device",
    sources: [SOURCES],
  };
}
