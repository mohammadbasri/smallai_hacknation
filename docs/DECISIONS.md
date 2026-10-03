# Decision log

Architecture and product decisions for the Small AI hackathon entry, one entry per decision.
Newest at the bottom. Status is one of **Proposed**, **Accepted**, **Superseded**, **Open**.
When a decision changes, do not edit the old entry: add a new one and mark the old one Superseded.

Format: context (why we had to decide), decision, consequences (what it costs us), alternatives considered.

---

## D-001 · Stack: React (Vite + TypeScript) frontend, Python (FastAPI) backend

- **Date:** 2026-10-03
- **Status:** Accepted

**Context.** Hackathon weekend of 3–4 October 2026. The brief welcomes vibe-coded builds. The team needs a stack that is fast to generate, fast to demo, and strong on small-model tooling.

**Decision.** React PWA for the UI, FastAPI for the API and any server-side model work.

**Consequences.**
- Python gives us the small-model ecosystem (ONNX, llama.cpp, scikit-learn, Hugging Face) and the easiest webhook handling for SMS/voice channels.
- A PWA installs without an app store and runs on whatever smartphone the team has.
- We depend on a browser for the UI, so a basic phone can only be reached through a channel adapter (see D-004).

**Alternatives considered.**
- Kotlin Android + TensorFlow Lite: best offline fidelity, too slow for a weekend, still assumes a smartphone.
- Flutter / React Native: native inference possible, toolchain cost with no demo gain over a PWA.
- Node/Express all-TypeScript: only worthwhile if inference is in-browser; loses the Python ML ecosystem.

---

## D-002 · Human-in-the-loop guardrail is a server-side decision with a fixed label list

- **Date:** 2026-10-03
- **Status:** Accepted

**Context.** Responsible AI is pass/fail in judging. The brief asks for "not sure, ask a person" instead of guessing, and recommends a fixed list of answers so output can be audited.

**Decision.** Every model returns a `(label, confidence)` where `label` comes from a fixed per-sector list. A single function (`guardrails.decide`) compares confidence against `CONFIDENCE_THRESHOLD` (default 0.65) and returns `answer` or `ask_a_person`. Below threshold the label is dropped and a localized fallback message is returned. The UI always shows the confidence meter.

**Consequences.**
- One place to tune and to show judges.
- Models must expose a calibrated confidence; a stub or an uncalibrated classifier makes the threshold meaningless. Calibration is a to-do once the real model lands.
- The fixed label list is published at `GET /api/inference/labels/{sector}` so the "complete set of things the tool may say" is inspectable.

**Alternatives considered.**
- Free-text generative answers with a disclaimer: fails the "fixed list" guidance and is hard to check for hallucination.
- Client-side threshold only: easy to bypass, and the SMS channel (D-004) has no client.

---

## D-003 · Offline strategy: cached app shell + localStorage store-and-forward queue

- **Date:** 2026-10-03
- **Status:** Accepted

**Context.** Rule 2 of the brief: the core feature works offline. Noor buys 3G bundles and the phone is often out of signal.

**Decision.** A hand-written service worker caches the app shell (cache-first, API calls excluded). Records captured while offline are saved in localStorage and flushed to `POST /api/sync` when `online` fires or on demand. The sync endpoint is idempotent on record id.

**Consequences.**
- Zero extra dependencies; bundle stays under 50 KB gzipped.
- localStorage is text-only and small (about 5 MB). Queuing images or audio needs IndexedDB. Switch when that need appears.
- `navigator.onLine` is optimistic, so the queue also catches request failures, not just the offline event.

**Alternatives considered.**
- Workbox / vite-plugin-pwa: more features, more config, another dependency to debug under time pressure.
- Background Sync API: not available on iOS Safari.

---

## D-004 · Where the model runs

- **Date:** 2026-10-03
- **Status:** Open (recommendation: shape 2)

**Context.** Noor's own device is a basic phone (calls, SMS, mobile money). She has a smartphone only on weekends. The brief says "runs on a device the user already has" and "core feature works offline". A server-side model behind a web app satisfies neither for Noor herself.

**Options.**
1. **Model in the browser.** ONNX Runtime Web or Transformers.js inside the React app. Backend shrinks to sync only. Honest offline story, but requires the smartphone and leaves Python nearly idle.
2. **Model on a local edge box.** FastAPI runs the model on a Raspberry Pi or laptop at the cooperative, clinic, or farm. Phones reach it over SMS, a voice line, or local Wi-Fi. React becomes the operator dashboard. Reaches a basic phone; uses Python where it is strongest; answers "would SMS do the same job?" by putting the AI behind the SMS.

**Recommendation.** Shape 2, with an SMS channel adapter (Africa's Talking or Twilio sandbox) as a FastAPI webhook router and a Pi-friendly Docker image.

**To decide before writing model code.** This choice determines whether inference code is TypeScript or Python.

---

## D-005 · Deployment: single container on Hugging Face Spaces (Docker)

- **Date:** 2026-10-03
- **Status:** Proposed

**Context.** Deployment is lightweight. We need HTTPS (service workers require it), no cold start during a demo, no credit card, and a place to keep model files.

**Decision.** FastAPI serves the built React `dist/` as static files. One multi-stage Dockerfile builds the frontend then copies it into the Python image. Deploy to a Hugging Face Space on port 7860.

**Consequences.**
- One URL, same origin, no CORS configuration in production.
- Free CPU tier sleeps only after 48 hours idle, so a judge's click-through does not hit a cold start.
- Model files up to GBs can live in the Space via Git LFS.
- Shape 2 of D-004 also needs the same image to run on the edge box; the Space is then the public demo mirror, not the "real" deployment.

**Alternatives considered.**
- Cloudflare Pages / Vercel (frontend) + Render free tier (backend): Render sleeps after 15 minutes and cold-starts in about a minute. Only worth it if the backend must scale independently.
- Fly.io / Railway: want a credit card.

---

## D-006 · Demo language: Swahili (sw) as placeholder

- **Date:** 2026-10-03
- **Status:** Proposed (replace with the language the team actually demos)

**Context.** Rule 4: at least one interaction in a named local language; judges will ask how the tool fares in a less-supported one.

**Decision.** Ship `en.json` and `sw.json` and a Swahili fallback message in the guardrail. Swahili was chosen as a widely supported placeholder (Common Voice, FLORES-200, MMS all cover it) so the i18n path can be exercised now.

**Consequences.**
- Adding a language is one JSON file plus one line in `i18n/index.ts` plus one fallback string in `guardrails.py`.
- The team must pick the real language and prepare an answer on a less-supported one (coverage in Common Voice hours, NLLB-200 BLEU, or MMS support).

---

## D-007 · Decisions and features are documented in-repo as we go

- **Date:** 2026-10-03
- **Status:** Accepted

**Context.** Judges score clarity and "what happens next". The video needs a crisp account of trade-offs, and the brief encourages entries that acknowledge them.

**Decision.** Every architectural or product decision gets an entry in this file. Every user-facing or judge-facing capability gets a row in `FEATURES.md` with a status. Both are updated in the same change that implements the decision or feature.

**Consequences.**
- Slight overhead per change.
- The video script and the "your take" section can be lifted straight from these files.
