# Karibu · Small AI for a farm-tour operator

**Hack-Nation × World Bank Group · Small AI for Development Hackathon 2026 · Sector: Tourism (Annex C)**

> Because of this tool, **Noor** will **understand and answer a visitor's enquiry in the visitor's language, from the phone she already has, the same day** that she would otherwise **answer late, through a guide, or not at all**; we know because the brief's Tourism scenario describes visitors who need a local guide to translate and an operator who never learns what worked, the GSMA Mobile Gender Gap Report shows the device such women own is most often a basic phone, and the World Bank's work with small operators in Jordan found the binding constraint was the missing digital listing and the skills to manage one.

Noor farms coffee in the Ondera highlands and hosts six or seven visitors a month by word of mouth. They write in
English or French; she reads Kiswahili. She has a basic phone for calls and SMS, and her daughter's smartphone at
weekends. Karibu reads the message for her, tells her in Kiswahili what the visitor wants, drafts a reply from a fixed
template that she approves, keeps her bookings, and turns visitor feedback into "keep doing / fix next".
**The AI reads; Noor answers.**

## What it does

| Workflow (Annex C) | How | Where it runs |
| --- | --- | --- |
| Responding to enquiries across languages | Detects language (en/fr/sw/other) and intent (9 fixed intents); renders the matching template in the visitor's language, shows Noor the meaning in Kiswahili; she copies/sends, sends a holding reply, writes her own, or dismisses | On the phone, offline · and over **SMS** for the basic phone |
| Managing a booking | Ledger with pending/confirmed/cancelled/completed; confirmation, reminder, cancellation and follow-up messages from templates | On the phone, offline |
| Learning from visitor feedback | Splits a review into clauses, tags each with an aspect (8 fixed) and polarity; aggregates into keep-doing / fix-next with an explicit "x of y parts were clear enough to count" | On the phone, offline |
| Becoming discoverable | Listing text in en/fr/sw generated from the farm profile only | On the phone, offline |

### The brief's rules

- **Runs on a device the user already has.** SMS channel for Noor's basic phone (she receives one Kiswahili SMS per enquiry and replies `1`, `2` or in her own words). PWA for the weekend smartphone, no app store.
- **Core feature works offline.** Models and templates (2.1 MB) are cached on first open; reading messages and feedback never needs a signal. Records queue and sync when a signal returns.
- **Model files small enough to side-load.** Four JSON models, 2.1 MB uncompressed (~1 MB gzipped), no WebAssembly, no GPU.
- **Local language.** Operator side in Kiswahili. Visitors answered in English, French or Kiswahili; other languages are flagged, not guessed. How it would fare in a less-supported language: see D-013 in [docs/DECISIONS.md](docs/DECISIONS.md).

### Guardrails (pass/fail)

- A person makes the final call: nothing reaches a visitor until Noor presses a button or replies by SMS.
- Below 65 % confidence the tool says "not sure" and suggests nothing. The `other` intent is never auto-answered.
- Every visitor-facing sentence comes from a fixed template list ([shared/templates/replies.json](shared/templates/replies.json), published at `GET /api/inference/replies`). The tool cannot invent a price or a road.
- Confidence and the full ranked score list are always on screen.

### Why AI and not SMS, a spreadsheet or a search

An SMS can carry the message; it cannot read "Pouvez-vous nous envoyer la position GPS ?" and tell Noor it is a
directions question. A spreadsheet cannot tell *price* from *cancel* in French. A search needs Noor to know what to
search for. Nine intents in three languages, with a confidence Noor can see, is exactly the size of problem a
small classifier solves and a rule list does not.

## Honest numbers

Hold-out on our own synthetic seed data (by pattern), threshold 0.65. Full detail in [docs/MODEL_CARD.md](docs/MODEL_CARD.md).

| Model | Accuracy | Answers (coverage) | Right when answering | Size |
| --- | --- | --- | --- | --- |
| intent | 0.80 | 69 % | 0.92 | 881 KB |
| langid | 0.99 | 97 % | 1.00 | 184 KB |
| aspect | 0.67 | 58 % | 0.84 | 950 KB |
| sentiment | 0.69 | 74 % | 0.72 | 139 KB |

All training data is synthetic (no real visitor traffic, no code-switching, team-written Swahili). The model card and
`GET /api/datasets` state what the data does not cover. The TypeScript and Python runtimes are proven identical by
`backend/tests/test_parity.py`.

## Run it

Windows: `start.bat` · macOS/Linux: `./start.sh` (installs, then runs API on :8000 and app on :5173).

Manual:

```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env
uvicorn app.main:app --reload --port 8000      # OpenAPI UI: http://localhost:8000/docs
pytest                                          # 20 tests

# frontend (another terminal)
cd frontend && npm install && npm run dev       # http://localhost:5173
```

Single container (what a Hugging Face Space or a Raspberry Pi at the cooperative runs):

```bash
docker build -t karibu . && docker run -p 7860:7860 -v karibu-data:/data karibu
docker buildx build --platform linux/arm64 -t karibu:pi .      # edge-box image
```

Retrain the models (needs scikit-learn): `cd backend && pip install -r ml/requirements.txt && python -m ml.train`.
This rewrites `shared/models/*.json` and `shared/models/METRICS.md`; the frontend copies `shared/` on every `dev`/`build`.

### Try the SMS channel

```bash
curl -X POST localhost:8000/api/sms/inbound -d "from=+447700900123" -d "text=How much is the coffee tour for 3?"
# -> Noor receives: "KARIBU: Ujumbe mpya kutoka +447700900123 (Kiingereza). Anauliza bei. ... Jibu 1 = tuma jibu la kawaida ..."
curl -X POST localhost:8000/api/sms/operator -d "from=+000000000000" -d "text=1"
# -> visitor receives the English price template; Noor receives "KARIBU: Jibu limetumwa"
curl localhost:8000/api/sms/outbox
```

Set `SMS_PROVIDER=africastalking` (or `twilio`) and the credentials in `.env` to send for real; `console` logs only.

## Layout

```
shared/                 ONE source of truth read by both runtimes
  models/*.json         four tiny models + METRICS.md (generated by backend/ml/train.py)
  templates/*.json      every sentence the tool may say to a visitor (en/fr/sw), operator labels, listing
backend/
  app/services/tinymodel.py   dependency-free model runtime (mirrors frontend/src/lib/tinyModel.ts)
  app/services/model.py       hub: analyse_enquiry, analyse_feedback
  app/services/replies.py     template rendering (fixed list of answers)
  app/services/store.py       SQLite (sync, enquiries, bookings, feedback, profile, SMS log)
  app/services/sms.py         gateway: console | africastalking | twilio
  app/routers/                health, inference, enquiries, feedback, bookings, profile, sms, sync, datasets
  ml/                         featurizer, seed data, trainer, parity probe
  tests/                      20 tests incl. TS/Python parity
frontend/
  src/lib/tinyModel.ts        browser model runtime
  src/lib/models.ts           load artifacts, analyse on device, render templates, summarise feedback
  src/lib/store.ts            offline state + sync queue
  src/pages/                  Inbox, Bookings, Feedback, Listing, Sms, About
  public/sw.js                caches app shell + /shared for offline use
docs/
  CHALLENGE_BRIEF.md  DECISIONS.md  FEATURES.md  MODEL_CARD.md  DATA_HANDLING.md  VIDEO_SCRIPT.md
Dockerfile              single image: Space / laptop / Raspberry Pi
```

## What localising AI development means to us

Not a bigger model that happens to speak Swahili. A small one shaped by Noor's constraints: her phone, her signal, her
language, her right to decide. The trade-off we chose, and say out loud: templates instead of translation means Noor
cannot yet type a free reply and have it translated. That is the next step, on the edge box, with NLLB-200 (F-34).
