# Model card · Karibu tiny models

Four small text classifiers that run identically in the browser (TypeScript) and on the server / edge box (Python).
Everything here is reproducible with `cd backend && python -m ml.train`; the metrics table is regenerated into
[`shared/models/METRICS.md`](../shared/models/METRICS.md) on every run.

## What they are

| Model | Task | Classes | Features | Shipped size |
| --- | --- | --- | --- | --- |
| `intent` | visitor enquiry → intent | 9 (`price`, `booking`, `availability`, `directions`, `whats_included`, `dietary_accessibility`, `cancel_change`, `thanks_feedback`, `other`) | word uni/bigrams + char 3–4-grams | 881 KB |
| `langid` | message → language | 4 (`en`, `fr`, `sw`, `other`) | same | 184 KB |
| `aspect` | review clause → what it is about | 9 (`coffee_tasting`, `farm_walk`, `food`, `guide_translation`, `price_value`, `access_road`, `hospitality`, `booking_communication`, `other`) | same | 950 KB |
| `sentiment` | review clause → polarity | 2 (`positive`, `negative`) | word uni/bigrams only | 139 KB |

Architecture: shared featurizer (lower-case, word unigrams and bigrams, word-boundary character 3- and 4-grams,
log-TF × smoothed IDF, L2 norm) → multinomial logistic regression → softmax. Weights are exported as plain JSON
(`vocab`, `idf`, `coef`, `intercept`). Total **2.1 MB uncompressed, about 1 MB gzipped**: side-loadable over a 3G
bundle in seconds, cached by the service worker on first open, no WebAssembly, no GPU, no network afterwards.

Why linear models and not a small transformer: a multilingual MiniLM is 100+ MB and needs an inference runtime;
a quantised one still needs WebAssembly and tens of MB. For nine fixed intents with a human in the loop, a
well-regularised linear model on character n-grams is the smallest thing that works across three languages,
and every weight can be inspected.

## Training data

**All training data is synthetic**, written by the team for this hackathon. There is no real visitor traffic in it.

- Enquiries: about 290 hand-written patterns across en/fr/sw and 9 intents, with slots (`{n}`, `{day}`, `{date}`,
  `{time}`, `{name}`) filled from per-language lists → ~1,060 sentences. Source: `backend/ml/data/intents*.py`.
- Language-id "other" class: 40 sentences in German, Spanish, Italian and Portuguese.
- Reviews: about 480 hand-written clauses (one aspect, one polarity each) in en/fr/sw, plus ~780 clauses generated
  from noun + adjective templates ("the lunch was cold", "chakula ilikuwa baridi"), used for **training only**.
  Source: `backend/ml/data/reviews*.py`, `augment.py`.

Style references (not ingested): MASSIVE intent taxonomy, Yelp Open Dataset review language, Wikivoyage vocabulary.

## Evaluation

Hold-out is **by pattern** for intent and langid (a sentence template is either entirely in train or entirely in
test) and stratified by class for aspect and sentiment, with augmented clauses excluded from the test pool.
The shipped artifact is then refit on all data. Threshold for "answer vs. ask a person": **0.65**.

| Model | Test n | Accuracy | Macro-F1 | Answers (coverage) | Accuracy when answering |
| --- | --- | --- | --- | --- | --- |
| intent | 263 | 0.80 | 0.76 | 69% | 0.92 |
| langid | 273 | 0.99 | 0.93 | 97% | 1.00 |
| aspect | 121 | 0.67 | 0.67 | 58% | 0.84 |
| sentiment | 112 | 0.69 | 0.68 | 74% | 0.72 |

Read the last two columns together: the tool answers ~70% of enquiries and is right ~92% of the time when it does;
the other ~30% are shown to Noor as "not sure" with no suggestion. Out-of-domain probes ("the quick brown fox",
"please transfer 5000 to account 1234", keyboard mash) all fall below the threshold.

**Variance.** The test sets are small (112–273 items). Aspect and sentiment move by ±5 points between random splits.
Treat the numbers as the right order of magnitude, not as precise.

## Known weaknesses (please read before trusting it)

1. **Sentiment is the weakest model.** Polarity in real reviews is often implicit ("we only got one tiny cup"); our
   synthetic data cannot teach that. Mitigation: only confident clauses count toward the summary and the skipped
   count is always displayed. Fix: fine-tune on Yelp Open Dataset polarity (English) and collect Swahili/French
   labelled clauses from real consenting visitors.
2. **No code-switching.** Real messages mix Swahili and English in one sentence. Not in the training data.
3. **No SMS shorthand, typos, emoji-only messages, voice notes.**
4. **Swahili was written by the team**, not sampled from native speakers' actual messages. Dialect and register
   coverage is unknown.
5. **Languages.** Only en/fr/sw are answered. de/es/it/pt are detected as "other" (and the visitor is politely asked to
   write in a supported language); any other language or script is unknown territory: it may be mis-detected as one
   of the four classes. A less-supported local language (e.g. Kikuyu, Luganda) would need ~100 patterns per intent
   to reach similar numbers, which a motivated speaker can write in an afternoon; the pipeline is unchanged.
6. **Intent confusions** cluster where the human action is the same anyway (`booking` ↔ `availability`,
   `price` ↔ `whats_included`); both lead to Noor confirming the facts.
7. **Templates, not translation.** Replies are pre-written in three languages; the tool cannot translate a free-text
   message Noor types. That is deliberate (no hallucination) and is the single biggest "what's next".

## Intended use and guardrails

- Informs a human operator; never sends anything on its own.
- Fixed label lists, published at `GET /api/inference/labels/{model}`; fixed reply templates at `GET /api/inference/replies`.
- Below threshold → "not sure", no suggestion, holding reply available.
- Confidence and the full ranked probability list are always shown.
- Not for: medical, legal or financial advice; anything beyond a farm-tour enquiry.
