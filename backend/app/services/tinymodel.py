"""Dependency-free runtime for the JSON model artifacts in shared/models/.

Mirrors frontend/src/lib/tinyModel.ts exactly. Any change to the featurizer must be made in
ml/featurizer.py, here, and in the TypeScript file, then the models re-exported.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

CHAR_NGRAMS = (3, 4)
_CONTRAST = re.compile(r"\s+(?:but|however|although|though|mais|pourtant|lakini|ila|ingawa)\s+", re.IGNORECASE)
_SENTENCE = re.compile(r"[.!?;\n]+")


def normalize(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(ch if (ch.isalnum() or ch.isspace() or ch == "'") else " ")
    return " ".join("".join(out).split())


def featurize(text: str, families: str = "wbc") -> Counter:
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


def split_clauses(text: str) -> list[str]:
    """Split a review into clauses at sentence ends and contrast words. Same rule as the browser runtime."""
    parts: list[str] = []
    for sentence in _SENTENCE.split(text):
        for clause in _CONTRAST.split(sentence):
            clause = clause.strip(" ,")
            if len(clause.split()) >= 2:
                parts.append(clause)
    return parts


@dataclass
class TinyModel:
    name: str
    version: str
    task: str
    classes: list[str]
    languages: list[str]
    vocab: dict[str, int]
    idf: list[float]
    coef: list[list[float]]
    intercept: list[float]
    threshold_hint: float
    metrics: dict
    notes: str
    size_bytes: int
    families: str = "wbc"

    @classmethod
    def load(cls, path: Path | str) -> "TinyModel":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            version=data["version"],
            task=data["task"],
            classes=data["classes"],
            languages=data.get("languages", []),
            vocab={f: i for i, f in enumerate(data["vocab"])},
            idf=data["idf"],
            coef=data["coef"],
            intercept=data["intercept"],
            threshold_hint=data.get("threshold_hint", 0.65),
            metrics=data.get("metrics_holdout", {}),
            notes=data.get("notes", ""),
            size_bytes=path.stat().st_size,
            families=data.get("feature_families", "wbc"),
        )

    def vector(self, text: str) -> dict[int, float]:
        vec: dict[int, float] = {}
        for f, c in featurize(text, self.families).items():
            idx = self.vocab.get(f)
            if idx is not None:
                vec[idx] = (1.0 + math.log(c)) * self.idf[idx]
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            for k in vec:
                vec[k] /= norm
        return vec

    def probabilities(self, text: str) -> list[float]:
        vec = self.vector(text)
        logits = []
        for row, b in zip(self.coef, self.intercept):
            z = b
            for idx, v in vec.items():
                z += row[idx] * v
            logits.append(z)
        m = max(logits)
        exps = [math.exp(z - m) for z in logits]
        s = sum(exps)
        return [e / s for e in exps]

    def predict(self, text: str) -> tuple[str, float, list[tuple[str, float]]]:
        """Returns (top label, confidence, ranked (label, prob) list)."""
        probs = self.probabilities(text)
        ranked = sorted(zip(self.classes, probs), key=lambda kv: -kv[1])
        return ranked[0][0], ranked[0][1], ranked

    def summary(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "task": self.task,
            "classes": self.classes,
            "languages": self.languages,
            "size_bytes": self.size_bytes,
            "vocab_size": len(self.vocab),
            "feature_families": self.families,
            "metrics_holdout": self.metrics,
            "notes": self.notes,
        }
