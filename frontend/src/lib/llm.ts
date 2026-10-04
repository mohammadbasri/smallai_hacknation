/** On-device Qwen via WebLLM. Weights download once, are cached by the browser, then work offline.
 *  The model writes the answer; confidence is the mean token probability. It replies UNSURE to defer to a person. */
import type { MLCEngineInterface } from "@mlc-ai/web-llm";
import type { InferenceResponse, Sector } from "../api/client";

export const MODEL_ID = "Qwen2.5-0.5B-Instruct-q4f16_1-MLC";

const SOURCES = "Qwen2.5-0.5B-Instruct running on this device";
const READY_KEY = "smallai.llm_ready";

let engine: MLCEngineInterface | null = null;
let loading: Promise<MLCEngineInterface> | null = null;

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
  return engine !== null;
}

export async function loadLLM(onProgress?: (fraction: number) => void): Promise<void> {
  if (engine) return;
  loading ??= import("@mlc-ai/web-llm")
    .then((webllm) => webllm.CreateMLCEngine(MODEL_ID, { initProgressCallback: (p) => onProgress?.(p.progress) }))
    .then((e) => {
      engine = e;
      try {
        localStorage.setItem(READY_KEY, MODEL_ID);
      } catch {
        /* ignore */
      }
      return e;
    })
    .finally(() => {
      loading = null;
    });
  await loading;
}

export async function askLocal(sector: Sector, text: string, language: string): Promise<InferenceResponse> {
  if (!engine) throw new Error("LLM not loaded");
  const reply = language === "sw" ? "Kiswahili" : "English";

  const res = await engine.chat.completions.create({
    messages: [
      {
        role: "system",
        content:
          `You are a helpful ${sector} assistant for visitors and small tourism operators in rural areas. ` +
          `Answer in ${reply}, in at most 3 short sentences. Give practical, honest advice. ` +
          `Never invent prices, opening times or phone numbers. ` +
          `If the message is not a tourism question, or you are not sure, reply with exactly: UNSURE`,
      },
      { role: "user", content: text },
    ],
    max_tokens: 200,
    temperature: 0.3,
    logprobs: true,
    top_logprobs: 1,
  });

  const choice = res.choices[0];
  const answer = (choice.message.content ?? "").trim();
  const lps = (choice.logprobs?.content ?? []).map((t) => t.logprob);
  const confidence = lps.length ? Math.exp(lps.reduce((a, b) => a + b, 0) / lps.length) : 0;
  const unsure = answer === "" || answer.toUpperCase().startsWith("UNSURE");

  return {
    decision: unsure ? "ask_a_person" : "answer",
    label: null,
    confidence: unsure ? 0 : confidence,
    explanation: unsure
      ? language === "sw"
        ? "Sina uhakika. Tafadhali muulize mtu (kiongozi wa watalii au afisa utalii)."
        : "Not sure. Please ask a person (a tour guide or tourism officer)."
      : answer,
    language,
    model_name: MODEL_ID,
    model_version: "on-device",
    sources: [SOURCES],
  };
}
