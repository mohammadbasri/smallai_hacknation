"""Train and export the four tiny models used by the tourism tool.

    cd backend && .venv/Scripts/python -m ml.train        (Windows)
    cd backend && .venv/bin/python -m ml.train            (macOS / Linux)

Models (all: shared featurizer -> TF-IDF -> multinomial logistic regression -> softmax):

  intent      visitor enquiry -> one of a fixed list of intents            (en, fr, sw)
  langid      message -> en | fr | sw | other                               (other = unsupported language)
  aspect      review clause -> one of a fixed list of experience aspects    (en, fr, sw)
  sentiment   review clause -> positive | negative

Artifacts are written to ../shared/models/*.json and are read by BOTH runtimes:
  backend/app/services/tinymodel.py   (Python, for the SMS channel and the API)
  frontend/src/lib/tinyModel.ts        (TypeScript, in the browser, offline)

Metrics are computed on a hold-out split made BY PATTERN (intent/langid) or stratified by class (aspect/sentiment),
then the final model is refit on all data. The report goes to ../shared/models/METRICS.md and is quoted in
docs/MODEL_CARD.md. Everything here is synthetic seed data; the model card says so.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from ml.data.intents import INTENTS, PATTERNS, SLOTS, UNSUPPORTED_LANGUAGE_SAMPLES
from ml.data.augment import generate as generate_augmented
from ml.data.reviews import ASPECTS, CLAUSES, POLARITIES
from ml.featurizer import features

SEED = 20261003
OUT_DIR = Path(__file__).resolve().parents[2] / "shared" / "models"
VERSION = "1.0.0"
THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.65"))
HOLDOUT = 0.25
FILLINGS_PER_PATTERN = 6

rng = random.Random(SEED)


# --------------------------------------------------------------------------- data building
def expand(pattern: str, lang: str) -> list[str]:
    slots = re.findall(r"{(\w+)}", pattern)
    if not slots:
        return [pattern]
    out = set()
    for _ in range(FILLINGS_PER_PATTERN):
        s = pattern
        for slot in slots:
            s = s.replace("{" + slot + "}", rng.choice(SLOTS[lang][slot]), 1)
        out.add(s)
    return sorted(out)


def build_intent_sets():
    """Returns (train, test) lists of (text, intent, lang). Split is by pattern."""
    train, test = [], []
    for lang, by_intent in PATTERNS.items():
        for intent, pats in by_intent.items():
            pats = list(pats)
            rng.shuffle(pats)
            n_test = max(1, round(len(pats) * HOLDOUT))
            for i, p in enumerate(pats):
                target = test if i < n_test else train
                for s in expand(p, lang):
                    target.append((s, intent, lang))
    return train, test


def build_langid_sets(intent_train, intent_test):
    train = [(t, lang) for t, _, lang in intent_train]
    test = [(t, lang) for t, _, lang in intent_test]
    unsupported = list(UNSUPPORTED_LANGUAGE_SAMPLES)
    rng.shuffle(unsupported)
    n_test = round(len(unsupported) * HOLDOUT)
    test += [(t, "other") for t in unsupported[:n_test]]
    train += [(t, "other") for t in unsupported[n_test:]]
    return train, test


def stratified_split(rows, label_index):
    by_label = defaultdict(list)
    for r in rows:
        by_label[r[label_index]].append(r)
    train, test = [], []
    for label, items in by_label.items():
        items = list(items)
        rng.shuffle(items)
        n_test = max(1, round(len(items) * HOLDOUT))
        test += items[:n_test]
        train += items[n_test:]
    return train, test


# --------------------------------------------------------------------------- vectorising
class Vocab:
    def __init__(self, texts: list[str], max_features: int, min_df: int = 1, families: str = "wbc"):
        self.families = families
        df: Counter = Counter()
        for t in texts:
            df.update(features(t, families).keys())
        n_docs = len(texts)
        ranked = sorted((f for f, d in df.items() if d >= min_df), key=lambda f: (-df[f], f))[:max_features]
        self.vocab = {f: i for i, f in enumerate(ranked)}
        self.idf = [math.log((1 + n_docs) / (1 + df[f])) + 1.0 for f in ranked]

    def transform(self, texts: list[str]) -> csr_matrix:
        rows, cols, vals = [], [], []
        for r, t in enumerate(texts):
            vec: dict[int, float] = {}
            for f, c in features(t, self.families).items():
                idx = self.vocab.get(f)
                if idx is not None:
                    vec[idx] = (1.0 + math.log(c)) * self.idf[idx]
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            for idx, v in vec.items():
                rows.append(r)
                cols.append(idx)
                vals.append(v / norm)
        return csr_matrix((vals, (rows, cols)), shape=(len(texts), len(self.vocab)))


# --------------------------------------------------------------------------- training
def fit(texts, labels, classes, max_features, C, families="wbc"):
    vocab = Vocab(texts, max_features=max_features, families=families)
    X = vocab.transform(texts)
    y = np.array([classes.index(l) for l in labels])
    clf = LogisticRegression(C=C, max_iter=2000)
    clf.fit(X, y)
    return vocab, clf


def evaluate(vocab, clf, classes, texts, labels, threshold):
    X = vocab.transform(texts)
    proba = clf.predict_proba(X)
    # predict_proba columns follow clf.classes_ (indices into `classes`)
    pred_idx = clf.classes_[proba.argmax(axis=1)]
    pred = [classes[i] for i in pred_idx]
    conf = proba.max(axis=1)
    covered = conf >= threshold
    acc = accuracy_score(labels, pred)
    f1 = f1_score(labels, pred, average="macro")
    cov = float(covered.mean()) if len(covered) else 0.0
    acc_cov = accuracy_score(np.array(labels)[covered], np.array(pred)[covered]) if covered.any() else float("nan")
    confusions = Counter((t, p) for t, p in zip(labels, pred) if t != p)
    return {
        "n_test": len(texts),
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(f1), 4),
        "coverage_at_threshold": round(cov, 4),
        "accuracy_when_answering": round(float(acc_cov), 4),
        "top_confusions": [f"{t} -> {p} ({n})" for (t, p), n in confusions.most_common(5)],
    }


def export(name, task, classes, vocab: Vocab, clf, metrics, n_train, notes, languages):
    order = list(clf.classes_)  # indices into classes
    coef = np.zeros((len(classes), len(vocab.vocab)))
    intercept = np.zeros(len(classes))
    if clf.coef_.shape[0] == 1:
        # Binary: sklearn stores one row (positive class = classes_[1]). softmax([0, z]) == sigmoid(z).
        coef[order[1]] = clf.coef_[0]
        intercept[order[1]] = clf.intercept_[0]
    else:
        for row, cls_idx in enumerate(order):
            coef[cls_idx] = clf.coef_[row]
            intercept[cls_idx] = clf.intercept_[row]
    artifact = {
        "name": name,
        "task": task,
        "version": VERSION,
        "trained_at": date.today().isoformat(),
        "featurizer": "tinymodel-v1 (log tf, smoothed idf, l2)",
        "feature_families": vocab.families,
        "classes": classes,
        "languages": languages,
        "threshold_hint": THRESHOLD,
        "n_train": n_train,
        "metrics_holdout": metrics,
        "notes": notes,
        "vocab": list(vocab.vocab.keys()),
        "idf": [round(v, 4) for v in vocab.idf],
        "coef": [[round(float(v), 4) for v in row] for row in coef],
        "intercept": [round(float(v), 4) for v in intercept],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path, path.stat().st_size


def train_one(name, task, classes, train_rows, test_rows, max_features, C, notes, languages, families="wbc"):
    tr_texts, tr_labels = [r[0] for r in train_rows], [r[1] for r in train_rows]
    te_texts, te_labels = [r[0] for r in test_rows], [r[1] for r in test_rows]
    vocab, clf = fit(tr_texts, tr_labels, classes, max_features, C, families)
    metrics = evaluate(vocab, clf, classes, te_texts, te_labels, THRESHOLD)
    # refit on everything for the shipped artifact
    all_texts, all_labels = tr_texts + te_texts, tr_labels + te_labels
    vocab, clf = fit(all_texts, all_labels, classes, max_features, C, families)
    path, size = export(name, task, classes, vocab, clf, metrics, len(all_texts), notes, languages)
    return metrics, size, len(train_rows), len(test_rows)


OOD_PROBES = [
    ("The quick brown fox jumps over the lazy dog", "intent"),
    ("Please transfer 5000 to account 1234", "intent"),
    ("asdf qwer zxcv", "intent"),
    ("Wie viel kostet die Tour?", "langid"),
]


def main():
    intent_train, intent_test = build_intent_sets()
    langid_train, langid_test = build_langid_sets(intent_train, intent_test)

    polar_rows = [(t, pol, lang) for t, lang, _, pol in CLAUSES if pol]
    aspect_rows = [(t, asp, lang) for t, lang, asp, _ in CLAUSES]
    aspect_train, aspect_test = stratified_split(aspect_rows, 1)
    sent_train, sent_test = stratified_split(polar_rows, 1)
    # Template augmentation goes into TRAINING ONLY; hand-written clauses remain the hold-out pool.
    augmented = generate_augmented()
    aspect_train += [(t, asp, lang) for t, lang, asp, _ in augmented]
    sent_train += [(t, pol, lang) for t, lang, _, pol in augmented]

    report = []
    specs = [
        ("intent", "visitor enquiry -> intent", INTENTS, intent_train, intent_test, 20000, 300.0,
         "Synthetic templated enquiries (en/fr/sw). Hold-out by pattern. Not real visitor traffic.", ["en", "fr", "sw"]),
        ("langid", "message -> language (en/fr/sw/other)", ["en", "fr", "sw", "other"], langid_train, langid_test, 4000, 10.0,
         "'other' trained on de/es/it/pt samples only; any other script or language is unknown territory.", ["en", "fr", "sw", "other"]),
        ("aspect", "review clause -> experience aspect", ASPECTS, aspect_train, aspect_test, 20000, 100.0,
         "Synthetic clauses modelled on review language plus noun+adjective template augmentation (train only). One aspect per clause; mixed clauses are split by the runtime.", ["en", "fr", "sw"]),
        ("sentiment", "review clause -> polarity", POLARITIES, sent_train, sent_test, 20000, 30.0,
         "Binary, word uni+bigram features only (char n-grams carried topic, not polarity). Trained on hand-written clauses plus template augmentation (train only). Neutral or mixed clauses fall below the threshold and are shown as 'unsure'.", ["en", "fr", "sw"], "wb"),
    ]
    for spec in specs:
        name, task, classes, tr, te, maxf, C, notes, langs = spec[:9]
        families = spec[9] if len(spec) > 9 else "wbc"
        m, size, ntr, nte = train_one(name, task, classes, tr, te, maxf, C, notes, langs, families)
        report.append((name, task, classes, m, size, ntr, nte))
        print(f"{name:10s} train={ntr:5d} test={nte:4d} acc={m['accuracy']:.3f} f1={m['macro_f1']:.3f} "
              f"cov@{THRESHOLD}={m['coverage_at_threshold']:.3f} acc|answer={m['accuracy_when_answering']:.3f} size={size/1024:.0f}KB")

    # Out-of-domain probes using the shipped artifacts through the same runtime the API uses.
    from app.services.tinymodel import TinyModel  # noqa: WPS433 (import here so ml/ has no app dependency otherwise)

    probes = []
    for text, model in OOD_PROBES:
        tm = TinyModel.load(OUT_DIR / f"{model}.json")
        label, conf, _ = tm.predict(text)
        probes.append((model, text, label, conf))

    lines = [
        "# Model metrics",
        "",
        f"Generated by `python -m ml.train` on {date.today().isoformat()}. Threshold used for coverage: {THRESHOLD}.",
        "All training data is synthetic seed data written for the hackathon (see `backend/ml/data/`).",
        "Hold-out is by pattern for intent/langid and stratified by class for aspect/sentiment; the shipped file is refit on all data.",
        "",
        "| Model | Task | Classes | Train | Test | Accuracy | Macro-F1 | Coverage @thr | Accuracy when answering | Size |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    total = 0
    for name, task, classes, m, size, ntr, nte in report:
        total += size
        lines.append(
            f"| {name} | {task} | {len(classes)} | {ntr} | {nte} | {m['accuracy']:.3f} | {m['macro_f1']:.3f} | "
            f"{m['coverage_at_threshold']:.3f} | {m['accuracy_when_answering']:.3f} | {size/1024:.0f} KB |"
        )
    lines += ["", f"Total artifact size: {total/1024:.0f} KB (uncompressed JSON; gzip roughly halves it).", ""]
    lines += ["## Most frequent hold-out confusions", ""]
    for name, _, _, m, _, _, _ in report:
        lines.append(f"- **{name}**: " + ("; ".join(m["top_confusions"]) if m["top_confusions"] else "none"))
    lines += ["", "## Out-of-domain probes (should fall below the threshold or land in `other`)", "",
              "| Model | Input | Top label | Confidence |", "| --- | --- | --- | --- |"]
    for model, text, label, conf in probes:
        lines.append(f"| {model} | {text} | {label} | {conf:.2f} |")
    (OUT_DIR / "METRICS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'METRICS.md'}")


if __name__ == "__main__":
    main()
