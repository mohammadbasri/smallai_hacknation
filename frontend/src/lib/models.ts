/** Loads the shared artifacts (models + templates) and performs the two analyses ON DEVICE.
 *  The backend does the same with the same files for the SMS channel; both apply the same threshold. */
import { splitClauses, TinyModel, type Artifact } from "./tinyModel";
import type { Profile } from "./store";

export type Decision = "answer" | "ask_a_person";
export type VisitorLang = "en" | "fr" | "sw";
export type OperatorLang = "en" | "sw";
export const SUPPORTED_VISITOR_LANGUAGES: VisitorLang[] = ["en", "fr", "sw"];

interface Replies {
  version: string;
  languages: string[];
  intents: Record<string, Record<string, string>>;
  special: Record<string, Record<string, string>>;
}
interface Labels {
  intents: Record<string, Record<string, string>>;
  aspects: Record<string, Record<string, string>>;
  sentiment: Record<string, Record<string, string>>;
  languages: Record<string, Record<string, string>>;
  operator_summary: Record<string, Record<string, string>>;
}
interface Listing {
  listing: Record<string, string>;
}

export interface Hub {
  intent: TinyModel;
  langid: TinyModel;
  aspect: TinyModel;
  sentiment: TinyModel;
  replies: Replies;
  labels: Labels;
  listing: Listing;
  threshold: number;
  totalBytes: number;
}

export interface EnquiryAnalysis {
  decision: Decision;
  language: string;
  language_confidence: number;
  language_supported: boolean;
  intent: string | null;
  confidence: number;
  ranked: { label: string; probability: number }[];
  reply_for_visitor: string | null;
  reply_for_operator: string | null;
  operator_summary: string;
  holding_reply: string;
  model_name: string;
  model_version: string;
}

export interface ClauseAnalysis {
  text: string;
  aspect: string | null;
  aspect_confidence: number;
  aspect_decision: Decision;
  sentiment: string | null;
  sentiment_confidence: number;
  sentiment_decision: Decision;
}

let hubPromise: Promise<Hub> | null = null;

async function fetchJson<T>(path: string): Promise<{ data: T; bytes: number }> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  const text = await res.text();
  return { data: JSON.parse(text) as T, bytes: text.length };
}

export function loadHub(): Promise<Hub> {
  if (!hubPromise) {
    hubPromise = (async () => {
      const [intent, langid, aspect, sentiment, replies, labels, listing] = await Promise.all([
        fetchJson<Artifact>("/shared/models/intent.json"),
        fetchJson<Artifact>("/shared/models/langid.json"),
        fetchJson<Artifact>("/shared/models/aspect.json"),
        fetchJson<Artifact>("/shared/models/sentiment.json"),
        fetchJson<Replies>("/shared/templates/replies.json"),
        fetchJson<Labels>("/shared/templates/labels.json"),
        fetchJson<Listing>("/shared/templates/listing.json"),
      ]);
      const im = new TinyModel(intent.data, intent.bytes);
      return {
        intent: im,
        langid: new TinyModel(langid.data, langid.bytes),
        aspect: new TinyModel(aspect.data, aspect.bytes),
        sentiment: new TinyModel(sentiment.data, sentiment.bytes),
        replies: replies.data,
        labels: labels.data,
        listing: listing.data,
        threshold: im.thresholdHint,
        totalBytes: intent.bytes + langid.bytes + aspect.bytes + sentiment.bytes,
      };
    })().catch((e) => {
      hubPromise = null;
      throw e;
    });
  }
  return hubPromise;
}

// ----------------------------------------------------------------------------- templates
export function render(template: string, values: object): string {
  return template.replace(/{(\w+)}/g, (_, k: string) => {
    const v = (values as Record<string, unknown>)[k];
    return v === undefined || v === null ? "" : String(v);
  });
}

const visitorLang = (hub: Hub, lang: string): string => (hub.replies.languages.includes(lang) ? lang : "en");
const opLang = (lang: string): OperatorLang => (lang === "sw" ? "sw" : "en");

export function label(hub: Hub, kind: keyof Labels, key: string, operatorLang: string): string {
  const block = (hub.labels[kind] as Record<string, Record<string, string>>)[key];
  if (!block) return key.replace(/_/g, " ");
  return block[opLang(operatorLang)] ?? block.en;
}

export function special(hub: Hub, name: string, lang: string, profile: Profile, extra: Record<string, unknown> = {}): string {
  return render(hub.replies.special[name][visitorLang(hub, lang)], { ...profile, ...extra });
}

export function listingText(hub: Hub, lang: string, profile: Profile): string {
  return render(hub.listing.listing[visitorLang(hub, lang)], profile);
}

// ----------------------------------------------------------------------------- enquiries
export function analyseEnquiry(hub: Hub, text: string, operatorLang: string, profile: Profile): EnquiryAnalysis {
  const thr = hub.threshold;
  const lid = hub.langid.predict(text);
  const supported = (SUPPORTED_VISITOR_LANGUAGES as string[]).includes(lid.label) && lid.confidence >= thr;
  const otherLanguage = lid.label === "other" && lid.confidence >= thr;
  const replyLang = supported ? lid.label : "en";

  const it = hub.intent.predict(text);
  let decision: Decision = it.confidence >= thr ? "answer" : "ask_a_person";
  if (it.label === "other") decision = "ask_a_person";

  let replyVisitor: string | null = null;
  let replyOperator: string | null = null;
  let summary: string;
  const os = hub.labels.operator_summary;
  const ol = opLang(operatorLang);

  if (otherLanguage) {
    summary = os.unsupported_language[ol];
    replyVisitor = special(hub, "unsupported_language", "en", profile);
    replyOperator = special(hub, "unsupported_language", operatorLang, profile);
    decision = "ask_a_person";
  } else if (!supported) {
    decision = "ask_a_person";
    summary = render(os.ask_a_person[ol], { pct: Math.round(Math.min(it.confidence, lid.confidence) * 100) });
  } else if (decision === "answer") {
    const block = hub.replies.intents[it.label];
    replyVisitor = render(block[visitorLang(hub, replyLang)], profile);
    replyOperator = render(block[visitorLang(hub, operatorLang)], profile);
    summary = render(os.answer[ol], {
      language: label(hub, "languages", lid.label, operatorLang),
      intent_label: label(hub, "intents", it.label, operatorLang),
    });
  } else {
    summary = render(os.ask_a_person[ol], { pct: Math.round(it.confidence * 100) });
  }

  return {
    decision,
    language: lid.label,
    language_confidence: lid.confidence,
    language_supported: supported,
    intent: decision === "answer" ? it.label : null,
    confidence: it.confidence,
    ranked: it.ranked,
    reply_for_visitor: replyVisitor,
    reply_for_operator: replyOperator,
    operator_summary: summary,
    holding_reply: special(hub, "holding", replyLang, profile),
    model_name: "karibu-tiny-linear",
    model_version: hub.intent.version,
  };
}

// ----------------------------------------------------------------------------- feedback
export function analyseFeedback(hub: Hub, text: string, language?: string): { language: string; clauses: ClauseAnalysis[] } {
  const thr = hub.threshold;
  const lang = language || hub.langid.predict(text).label;
  const clauses = splitClauses(text).map((clause) => {
    const a = hub.aspect.predict(clause);
    const s = hub.sentiment.predict(clause);
    const ad: Decision = a.confidence >= thr ? "answer" : "ask_a_person";
    const sd: Decision = s.confidence >= thr ? "answer" : "ask_a_person";
    return {
      text: clause,
      aspect: ad === "answer" ? a.label : null,
      aspect_confidence: a.confidence,
      aspect_decision: ad,
      sentiment: sd === "answer" ? s.label : null,
      sentiment_confidence: s.confidence,
      sentiment_decision: sd,
    };
  });
  return { language: lang, clauses };
}

export interface AspectSummary {
  aspect: string;
  positive: number;
  negative: number;
  examples_positive: string[];
  examples_negative: string[];
}
export interface FeedbackSummary {
  n_reviews: number;
  n_clauses: number;
  n_confident: number;
  n_unsure: number;
  keep_doing: AspectSummary[];
  fix_next: AspectSummary[];
  aspects: AspectSummary[];
}

export function summarise(hub: Hub, reviews: { clauses: ClauseAnalysis[] }[]): FeedbackSummary {
  const pos: Record<string, string[]> = {};
  const neg: Record<string, string[]> = {};
  let n = 0;
  let conf = 0;
  for (const r of reviews) {
    for (const c of r.clauses) {
      n++;
      if (c.aspect && c.sentiment) {
        conf++;
        const bucket = c.sentiment === "positive" ? pos : neg;
        (bucket[c.aspect] ??= []).push(c.text);
      }
    }
  }
  const aspects = hub.aspect.classes
    .filter((a) => a !== "other")
    .map((a) => ({
      aspect: a,
      positive: (pos[a] ?? []).length,
      negative: (neg[a] ?? []).length,
      examples_positive: (pos[a] ?? []).slice(0, 3),
      examples_negative: (neg[a] ?? []).slice(0, 3),
    }));
  const keep = aspects.filter((r) => r.positive > r.negative).sort((a, b) => b.positive - b.negative - (a.positive - a.negative)).slice(0, 3);
  const fix = aspects.filter((r) => r.negative > 0).sort((a, b) => b.negative - a.negative).slice(0, 3);
  return { n_reviews: reviews.length, n_clauses: n, n_confident: conf, n_unsure: n - conf, keep_doing: keep, fix_next: fix, aspects };
}
