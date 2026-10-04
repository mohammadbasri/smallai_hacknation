# Feature register

Living list of what the tool does, what it will do, and why. Update in the same change that adds or alters a feature.
Each feature links to the decision(s) that shaped it in `DECISIONS.md` and to the brief rule or judging criterion it serves.

Sector: **Tourism** (D-008). Status: **Done** (built and tested), **Ready** (built, not yet exercised in the field), **In progress**, **Planned**, **Dropped**.

## Operator app (PWA, runs on the weekend smartphone, offline)

| ID | Feature | Status | Brief rule / criterion | Decision | Where |
| --- | --- | --- | --- | --- | --- |
| F-24 | Inbox: paste a visitor message, get language + intent + confidence, in Kiswahili | Done | Local language; clarity | D-008, D-009, D-011 | `frontend/src/pages/Inbox.tsx`, `lib/models.ts` |
| F-25 | Fixed-template reply in the visitor's language (en/fr/sw) with the meaning shown in Noor's language; copy & mark sent, holding reply, own reply, dismiss | Done | Fixed list of answers; human in the loop | D-010 | `shared/templates/replies.json`, `Inbox.tsx` |
| F-04 | "Not sure, read it yourself" below threshold; `other` intent never auto-answered; unsupported language flagged with a polite fixed note | Done | Guardrails (pass/fail) | D-002, D-013 | `lib/models.ts`, `backend/app/services/model.py` |
| F-05 | Confidence meter with threshold marker and full ranked score list | Done | Avoid hallucinations; clarity | D-002 | `components/Confidence.tsx` |
| F-26 | Booking ledger: add (incl. from an enquiry), confirm, cancel, complete; confirmation / reminder / cancellation / follow-up messages from templates | Done | Business workflow (Annex C) | D-010 | `pages/Bookings.tsx` |
| F-27 | Feedback: clause split, aspect + polarity per clause with "unsure", saved reviews, "keep doing / fix next" summary with coverage line | Done | Learning from visitor feedback (Annex C) | D-011 | `pages/Feedback.tsx` |
| F-28 | Farm profile + generated listing text in en/fr/sw (discoverability) | Done | Becoming discoverable (Annex C) | D-010 | `pages/Listing.tsx`, `shared/templates/listing.json` |
| F-31 | About page: rules checklist, guardrails, models with size and hold-out metrics, data sources with gaps, data handling | Done | Clarity; data grounding | D-007 | `pages/About.tsx` |
| F-07 | Offline app shell + models + templates cached by service worker on first load | Done | Core feature works offline | D-003, D-009 | `frontend/public/sw.js` |
| F-08 | Store-and-forward queue (enquiries, bookings, feedback, profile), auto-flush every 15 s when online, "Send now" | Done | Offline | D-003, D-012 | `lib/offlineQueue.ts`, `lib/store.ts` |
| F-09 | Online / offline badge | Done | Clarity | D-003 | `components/OnlineBadge.tsx` |
| F-10 | Operator UI in Kiswahili (default) and English | Done | Local language | D-013 | `src/i18n/` |
| F-02 | Voice input via phone keyboard dictation | Done (no code) | Voice | D-006 | any text field |

## Models

| ID | Feature | Status | Brief rule / criterion | Decision | Where |
| --- | --- | --- | --- | --- | --- |
| F-14 | Four tiny linear models (intent, langid, aspect, sentiment) trained from synthetic seed data, exported as JSON | Done | Small AI fidelity (25%) | D-011 | `backend/ml/`, `shared/models/` |
| F-15 | Calibration: threshold 0.65 evaluated as coverage vs accuracy-when-answering on hold-out; OOD probes | Done | Avoid hallucinations | D-002, D-011 | `shared/models/METRICS.md`, `docs/MODEL_CARD.md` |
| F-30 | Cross-runtime parity test (TypeScript vs Python give identical predictions) | Done | Evidence it works | D-011 | `backend/tests/test_parity.py`, `frontend/scripts/parity.mjs` |
| F-32 | Model card with data provenance, hold-out metrics and known weaknesses | Done | Data grounding (15%) | D-007 | `docs/MODEL_CARD.md` |
| F-06 | Fixed label lists and complete reply-template set published by the API | Done | Fixed list of answers | D-002 | `GET /api/inference/labels/{model}`, `GET /api/inference/replies` |

## Channel for the basic phone (edge box / server)

| ID | Feature | Status | Brief rule / criterion | Decision | Where |
| --- | --- | --- | --- | --- | --- |
| F-16 | SMS channel: inbound webhook (Africa's Talking / Twilio / JSON), Kiswahili notification to Noor with numbered options, Noor replies 1 / 2 / own words, visitor gets fixed reply | Done (console gateway); Ready (real gateways wired, untested with live credentials) | Runs on a device the user already has | D-009 | `backend/app/routers/sms.py`, `services/sms.py` |
| F-29 | SMS simulator page in the app showing the full message log | Done | Evidence it works | D-009 | `pages/Sms.tsx` |
| F-20 | SQLite persistence (sync records, enquiries, bookings, feedback, profile, SMS log); sync applies records to tables | Done | Scalability (10%) | D-012 | `backend/app/services/store.py` |
| F-12 | Health + models + OpenAPI docs | Done | Evidence it works | D-001 | `/api/health`, `/api/inference/models`, `/docs` |
| F-13 | Backend test suite (20 tests: guardrails, SMS round-trip, bookings, feedback, sync idempotence, datasets, parity) | Done | Evidence it works | — | `backend/tests/` |
| F-11 | Dataset citations in two layers (problem evidence / build data) with license, size, use and coverage gaps | Done | Data grounding | D-007 | `backend/app/routers/datasets.py` |
| F-23 | Data-handling statement | Done | Responsible AI (pass/fail) | — | `docs/DATA_HANDLING.md` |

## Deployment

| ID | Feature | Status | Brief rule / criterion | Decision | Where |
| --- | --- | --- | --- | --- | --- |
| F-19 | Single-container image (frontend + API + models), port 7860 for Hugging Face Spaces | Ready (image defined and built locally; Space not yet created) | Evidence it works | D-014 | `Dockerfile` |
| F-18 | Edge-box image (arm64 via `docker buildx`), stdlib-only runtime | Ready (not tested on a Pi) | Offline; on-device | D-009, D-014 | `Dockerfile` |

## Planned

| ID | Feature | Status | Why / what it needs |
| --- | --- | --- | --- |
| F-17 | Voice line (IVR) in Kiswahili on the edge box | Planned | Common Voice sw + MMS ASR; after the SMS channel is in the field |
| F-33 | Retention: auto-delete handled enquiries / completed bookings after 12 months | Planned | Data handling |
| F-34 | Free-text translation of Noor's own replies on the edge box (NLLB-200 distilled) | Planned | Biggest "what's next"; too large for the phone (D-010) |
| F-35 | Fine-tune sentiment on Yelp Open Dataset; collect consenting real feedback in sw/fr | Planned | Weakest model (model card) |
| F-36 | Ingest MASSIVE utterances as extra `other` negatives | Planned | Robustness to off-topic messages |

## Dropped

| ID | Feature | Reason | Decision |
| --- | --- | --- | --- |
| F-01 | Sector selector | Sector fixed to Tourism | D-008 |
| F-03 | Generic per-sector inference endpoint | Replaced by `/inference/enquiry` and `/inference/feedback` | D-008 |
| F-21 | IndexedDB media queue | No image or audio input in the tourism tool | D-003 |
| F-22 | Replace Swahili placeholder | Swahili confirmed as the demo language | D-013 |
| — | Workbox / vite-plugin-pwa | Extra dependency for no weekend benefit | D-003 |
| — | Free-text generative answers | Not auditable; fails fixed-list guidance | D-002, D-010 |
| — | Runtime machine translation on the phone | NLLB-200 ~1.2 GB; not side-loadable | D-010 |
| — | Native mobile app | Toolchain cost exceeds demo benefit | D-001 |
