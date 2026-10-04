"""Featurizer shared by training (Python), the backend runtime (Python) and the browser runtime (TypeScript).

The spec is deliberately tiny so it can be re-implemented exactly in frontend/src/lib/tinyModel.ts:

  1. lowercase; replace every character that is not a letter, digit, whitespace or apostrophe with a space
  2. tokens = split on whitespace
  3. features:
       w:<token>                 word unigram
       b:<token>_<next token>    word bigram
       c:<ngram>                 character 3- and 4-grams over " token " (word-boundary aware)
  4. x[i] = (1 + ln(count)) * idf[i] for features in the vocabulary, then L2-normalise

Any change here MUST be mirrored in tinyModel.ts and the models re-exported (python -m ml.train).
"""
from __future__ import annotations

import math
from collections import Counter

CHAR_NGRAMS = (3, 4)


def normalize(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum() or ch.isspace() or ch == "'":
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


def features(text: str, families: str = "wbc") -> Counter:
    """`families` selects feature groups: w = word unigrams, b = word bigrams, c = char n-grams."""
    counts: Counter = Counter()
    toks = normalize(text).split()
    for i, tok in enumerate(toks):
        if "w" in families:
            counts["w:" + tok] += 1
        if "b" in families and i + 1 < len(toks):
            counts["b:" + tok + "_" + toks[i + 1]] += 1
        if "c" in families:
            padded = " " + tok + " "
            for n in CHAR_NGRAMS:
                for j in range(0, max(0, len(padded) - n + 1)):
                    counts["c:" + padded[j : j + n]] += 1
    return counts


def vectorize(counts: Counter, vocab: dict[str, int], idf: list[float]) -> dict[int, float]:
    """Sparse TF-IDF vector (index -> value), L2-normalised."""
    vec: dict[int, float] = {}
    for f, c in counts.items():
        idx = vocab.get(f)
        if idx is None:
            continue
        vec[idx] = (1.0 + math.log(c)) * idf[idx]
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm > 0:
        for k in vec:
            vec[k] /= norm
    return vec
