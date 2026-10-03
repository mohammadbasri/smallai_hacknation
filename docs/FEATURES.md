# Feature register

Living list of what the tool does, what it will do, and why. Update in the same change that adds or alters a feature.
Each feature links to the decision(s) that shaped it in `DECISIONS.md` and to the brief rule or judging criterion it serves.

Status: **Done** (built and tested), **In progress**, **Planned**, **Dropped**.

| ID | Feature | Status | Brief rule / criterion | Decision | Where |
| --- | --- | --- | --- | --- | --- |
| F-01 | Sector selector (Health / Agriculture / Tourism) | Done | Pick one sector | D-001 | `frontend/src/components/SectorPicker.tsx` |
| F-02 | Text input for the situation (voice via phone keyboard dictation) | Done | Local-language interaction | D-006 | `frontend/src/pages/Home.tsx` |
| F-03 | Inference endpoint returning label + confidence from a fixed list | Done | Fixed list of answers | D-002 | `backend/app/routers/inference.py`, `services/model.py` |
| F-04 | Human-in-the-loop fallback: "not sure, ask a person" below threshold | Done | Guardrails (pass/fail) | D-002 | `backend/app/services/guardrails.py`, `frontend/src/components/ResultCard.tsx` |
| F-05 | Confidence meter always visible, model name and version shown | Done | Avoid hallucinations; clarity | D-002 | `frontend/src/components/ResultCard.tsx` |
| F-06 | Published label list per sector (`GET /api/inference/labels/{sector}`) | Done | Fixed list of answers | D-002 | `backend/app/routers/inference.py` |
| F-07 | Offline app shell via service worker | Done | Core feature works offline | D-003 | `frontend/public/sw.js`, `src/main.tsx` |
| F-08 | Store-and-forward queue, auto-flush on reconnect, manual "Send now" | Done | Core feature works offline | D-003 | `frontend/src/lib/offlineQueue.ts`, `backend/app/routers/sync.py` |
| F-09 | Online / offline badge | Done | Clarity, design | D-003 | `frontend/src/components/OnlineBadge.tsx` |
| F-10 | English + Swahili UI strings and guardrail messages, language switcher | Done | Local-language interaction | D-006 | `frontend/src/i18n/`, `backend/app/services/guardrails.py` |
| F-11 | Dataset citations with license and declared coverage gaps | Done | Data grounding (15%) | D-007 | `backend/app/routers/datasets.py` |
| F-12 | Health endpoint and OpenAPI docs | Done | Evidence it works | D-001 | `backend/app/routers/health.py`, `/docs` |
| F-13 | Backend test suite (guardrail, idempotent sync, dataset filter) | Done | Evidence it works | D-002, D-003 | `backend/tests/test_api.py` |
| F-14 | Real small model replacing the keyword stub | Planned | Small AI fidelity (25%) | D-004 (open) | `backend/app/services/model.py` or in-browser |
| F-15 | Confidence calibration for the real model | Planned | Avoid hallucinations | D-002 | with F-14 |
| F-16 | SMS channel adapter (webhook router) so a basic phone can use the tool | Planned | Runs on a device the user already has | D-004 shape 2 | `backend/app/routers/sms.py` (to create) |
| F-17 | Voice channel (IVR) in the local language | Planned | Local-language interaction by voice | D-004, D-006 | to decide after F-16 |
| F-18 | Edge-box deployment (Raspberry Pi / laptop) image | Planned | Offline; on-device | D-004 shape 2, D-005 | `backend/Dockerfile` (arm64 variant) |
| F-19 | Single-container public demo on Hugging Face Spaces | Planned | Evidence it works | D-005 | root `Dockerfile` + static mount in `main.py` |
| F-20 | Persistent sync store (SQLite) replacing in-memory dict | Planned | Scalability (10%) | D-003 | `backend/app/routers/sync.py` |
| F-21 | IndexedDB queue for images / audio | Planned (only if F-14 needs media input) | Offline | D-003 | `frontend/src/lib/offlineQueue.ts` |
| F-22 | Replace Swahili placeholder with the demo language; prepare the "less-supported language" answer | Planned | Local-language interaction | D-006 | `frontend/src/i18n/`, `guardrails.py` |
| F-23 | Data-handling statement (where data sits, who reads it, lost or shared phone) | Planned (required if Health) | Responsible AI (pass/fail) | — | `docs/DATA_HANDLING.md` (to create) |

## Dropped

| ID | Feature | Reason | Decision |
| --- | --- | --- | --- |
| — | Workbox / vite-plugin-pwa | Extra dependency and config for no weekend benefit | D-003 |
| — | Free-text generative answers | Not auditable; fails fixed-list guidance | D-002 |
| — | Native mobile app (Kotlin / Flutter / React Native) | Toolchain cost exceeds demo benefit in a weekend | D-001 |
