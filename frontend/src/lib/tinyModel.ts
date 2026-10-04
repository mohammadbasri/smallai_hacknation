/** Browser runtime for the JSON model artifacts in /shared/models.
 *
 *  Mirrors backend/app/services/tinymodel.py EXACTLY. If you change the featurizer, change both and re-export
 *  the models with `python -m ml.train`. No dependencies, no WebAssembly: a few hundred KB of JSON and arithmetic. */

export interface Artifact {
  name: string;
  task: string;
  version: string;
  trained_at: string;
  feature_families?: string;
  classes: string[];
  languages: string[];
  threshold_hint: number;
  n_train: number;
  metrics_holdout: Record<string, unknown>;
  notes: string;
  vocab: string[];
  idf: number[];
  coef: number[][];
  intercept: number[];
}

const CHAR_NGRAMS = [3, 4];
const ALLOWED = /[\p{L}\p{N}\s']/u;
const CONTRAST = /\s+(?:but|however|although|though|mais|pourtant|lakini|ila|ingawa)\s+/i;
const SENTENCE = /[.!?;\n]+/;

export function normalize(text: string): string {
  let out = "";
  for (const ch of text.toLowerCase()) out += ALLOWED.test(ch) ? ch : " ";
  return out.split(/\s+/).filter(Boolean).join(" ");
}

export function featurize(text: string, families = "wbc"): Map<string, number> {
  const counts = new Map<string, number>();
  const bump = (k: string) => counts.set(k, (counts.get(k) ?? 0) + 1);
  const toks = normalize(text).split(" ").filter(Boolean);
  toks.forEach((tok, i) => {
    if (families.includes("w")) bump("w:" + tok);
    if (families.includes("b") && i + 1 < toks.length) bump("b:" + tok + "_" + toks[i + 1]);
    if (families.includes("c")) {
      const padded = Array.from(" " + tok + " "); // code points, like Python str indexing
      for (const n of CHAR_NGRAMS) {
        for (let j = 0; j <= padded.length - n; j++) bump("c:" + padded.slice(j, j + n).join(""));
      }
    }
  });
  return counts;
}

/** Split a review into clauses at sentence ends and contrast words. Same rule as the Python runtime. */
export function splitClauses(text: string): string[] {
  const parts: string[] = [];
  for (const sentence of text.split(SENTENCE)) {
    for (let clause of sentence.split(CONTRAST)) {
      clause = clause.replace(/^[\s,]+|[\s,]+$/g, "");
      if (clause.split(/\s+/).filter(Boolean).length >= 2) parts.push(clause);
    }
  }
  return parts;
}

export class TinyModel {
  readonly name: string;
  readonly version: string;
  readonly task: string;
  readonly classes: string[];
  readonly languages: string[];
  readonly thresholdHint: number;
  readonly metrics: Record<string, unknown>;
  readonly notes: string;
  readonly families: string;
  readonly sizeBytes: number;
  private vocab: Map<string, number>;
  private idf: number[];
  private coef: number[][];
  private intercept: number[];

  constructor(a: Artifact, sizeBytes = 0) {
    this.name = a.name;
    this.version = a.version;
    this.task = a.task;
    this.classes = a.classes;
    this.languages = a.languages ?? [];
    this.thresholdHint = a.threshold_hint ?? 0.65;
    this.metrics = a.metrics_holdout ?? {};
    this.notes = a.notes ?? "";
    this.families = a.feature_families ?? "wbc";
    this.sizeBytes = sizeBytes;
    this.vocab = new Map(a.vocab.map((f, i) => [f, i]));
    this.idf = a.idf;
    this.coef = a.coef;
    this.intercept = a.intercept;
  }

  vector(text: string): Map<number, number> {
    const vec = new Map<number, number>();
    for (const [f, c] of featurize(text, this.families)) {
      const idx = this.vocab.get(f);
      if (idx !== undefined) vec.set(idx, (1 + Math.log(c)) * this.idf[idx]);
    }
    let norm = 0;
    for (const v of vec.values()) norm += v * v;
    norm = Math.sqrt(norm);
    if (norm > 0) for (const [k, v] of vec) vec.set(k, v / norm);
    return vec;
  }

  probabilities(text: string): number[] {
    const vec = this.vector(text);
    const logits = this.coef.map((row, r) => {
      let z = this.intercept[r];
      for (const [idx, v] of vec) z += row[idx] * v;
      return z;
    });
    const m = Math.max(...logits);
    const exps = logits.map((z) => Math.exp(z - m));
    const s = exps.reduce((a, b) => a + b, 0);
    return exps.map((e) => e / s);
  }

  /** Returns top label, its probability and the full ranked list (so the choice is inspectable). */
  predict(text: string): { label: string; confidence: number; ranked: { label: string; probability: number }[] } {
    const probs = this.probabilities(text);
    const ranked = this.classes.map((label, i) => ({ label, probability: probs[i] })).sort((a, b) => b.probability - a.probability);
    return { label: ranked[0].label, confidence: ranked[0].probability, ranked };
  }
}
