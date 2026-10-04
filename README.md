# Small AI for Development · Hackathon Boilerplate

React (Vite + TypeScript) frontend and Python (FastAPI) backend, shaped by the rules in the
Hack-Nation × World Bank *Small AI for Development* concept note (`file.pdf`, summarised in
[docs/CHALLENGE_BRIEF.md](docs/CHALLENGE_BRIEF.md)).

What the boilerplate already does for you:

| Brief requirement | Where it lives |
| --- | --- |
| Core feature works offline | `frontend/public/sw.js` caches the app shell; `src/lib/offlineQueue.ts` is store-and-forward |
| Local-language interaction (name the language) | `frontend/src/i18n/` (English + Hindi), `backend/app/services/guardrails.py` fallback messages |
| Human in the loop, no guessing | `backend/app/services/guardrails.py` returns `ask_a_person` below `CONFIDENCE_THRESHOLD`; `ResultCard.tsx` always shows confidence |
| Fixed list of answers | `backend/app/services/model.py` labels per sector, exposed at `GET /api/inference/labels/{sector}` |
| Cite datasets and their gaps | `backend/app/routers/datasets.py` (`coverage_gaps` is a required field) |
| Small, side-loadable model files | `MODEL_DIR` setting; swap `StubModel` for a quantized ONNX / TFLite / llama.cpp model |

## Layout

```
backend/            FastAPI app
  app/main.py       app factory, CORS, router wiring (all routes under /api)
  app/config.py     settings from .env
  app/schemas.py    Pydantic models (Sector, InferenceRequest/Response, Sync, Dataset)
  app/routers/      health, inference, sync (store-and-forward), datasets
  app/services/     model.py (adapter + stub), guardrails.py (human-in-the-loop)
  tests/            pytest suite
frontend/           Vite + React + TS
  src/api/client.ts typed API client
  src/i18n/         en.json, hi.json, tiny i18n hook
  src/lib/          offlineQueue.ts
  src/components/   ResultCard, OnlineBadge, LanguageSwitcher
  src/pages/Home.tsx
  public/sw.js      offline app-shell service worker
docs/CHALLENGE_BRIEF.md   rules, judging weights, deliverables, datasets from the PDF
docs/DECISIONS.md         decision log (ADR style): why the stack, guardrails, offline, deployment look this way
docs/FEATURES.md          feature register with status, mapped to brief rules and decisions
docker-compose.yml
```

## Run it

### Quickest: one script per platform

Requires Python 3.11+ and Node 18+ installed. The script creates the backend virtualenv, installs
Python and npm packages, copies `backend/.env.example` to `backend/.env` (if missing), then starts both
servers and opens http://localhost:5173 in your browser. Safe to re-run; installs are skipped when
already up to date.

Windows (double-click or run from a terminal):

```bat
start.bat          :: install anything missing, then run (two console windows: backend :8000, frontend :5173)
start.bat setup    :: install only
```

macOS / Linux:

```bash
chmod +x start.sh   # once
./start.sh          # install anything missing, then run both servers; Ctrl+C stops both
./start.sh setup    # install only
```

### Manual

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
# OpenAPI UI: http://localhost:8000/docs
pytest
```

Frontend (Node 18+):

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173  (Vite proxies /api -> http://localhost:8000)
```

Or both with Docker:

```bash
docker compose up --build
# frontend http://localhost:5173, backend http://localhost:8000
```

## Try the guardrail

```bash
curl -X POST http://localhost:8000/api/inference \
  -H "Content-Type: application/json" \
  -d '{"sector":"tourism","text":"how much is the tour, I want to book","language":"en"}'
# -> decision: "answer", label: "booking_request" or "price_enquiry"

curl -X POST http://localhost:8000/api/inference \
  -H "Content-Type: application/json" \
  -d '{"sector":"tourism","text":"something unclear","language":"hi"}'
# -> decision: "ask_a_person", explanation in Hindi
```

## Where to plug in your work

1. **Model**: implement the `SmallModel` protocol in `backend/app/services/model.py` and register it in `get_model`.
   For true offline inference, run the model in the browser instead (ONNX Runtime Web, TF.js, WebLLM) and keep
   the API for sync only. The `TODO` in `frontend/src/pages/Home.tsx` marks the spot.
2. **Language**: add `frontend/src/i18n/<code>.json`, register it in `i18n/index.ts`, and add the fallback message
   in `guardrails.py`. The demo language is Hindi.
3. **Datasets**: fill `backend/app/routers/datasets.py` with what you really trained on, including license and gaps.
4. **Persistence**: `routers/sync.py` is in-memory. Replace with SQLite/Postgres or forward to DHIS2 etc.
5. **Submission**: see the deliverables checklist in `docs/CHALLENGE_BRIEF.md`.
