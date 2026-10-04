"""Model adapter.

Replace `StubModel` with your real small model (quantized ONNX / TFLite / llama.cpp / sklearn...).
Keep the interface: `predict(text, language) -> Prediction` with a confidence in [0, 1]
and a label drawn from a FIXED list, so the guardrails in guardrails.py can do their job.
"""
from dataclasses import dataclass, field
from typing import Protocol

from app.schemas import Sector


@dataclass
class Prediction:
    label: str | None
    confidence: float
    explanation: str
    sources: list[str] = field(default_factory=list)


class SmallModel(Protocol):
    name: str
    version: str
    labels: list[str]

    def predict(self, text: str, language: str) -> Prediction: ...


# ---------------------------------------------------------------------------
# Stub implementation: keyword matching against a fixed list of answers.
# It exists only so the API works end to end before you plug in a model.
# ---------------------------------------------------------------------------

_SECTOR_LABELS: dict[Sector, dict[str, list[str]]] = {
    Sector.tourism: {
        "booking_request": ["book", "visit", "tour", "ziara", "come"],
        "price_enquiry": ["price", "cost", "bei", "how much"],
        "directions": ["where", "directions", "wapi", "road"],
    },
}


class StubModel:
    name = "stub-keyword-classifier"
    version = "0.0.1"

    def __init__(self, sector: Sector):
        self.sector = sector
        self.labels = list(_SECTOR_LABELS[sector].keys())

    def predict(self, text: str, language: str) -> Prediction:
        lowered = text.lower()
        scores = {
            label: sum(1 for kw in keywords if kw in lowered)
            for label, keywords in _SECTOR_LABELS[self.sector].items()
        }
        best_label, hits = max(scores.items(), key=lambda kv: kv[1])
        if hits == 0:
            return Prediction(
                label=None,
                confidence=0.0,
                explanation="No known pattern matched the input.",
                sources=[],
            )
        confidence = min(0.5 + 0.2 * hits, 0.95)
        return Prediction(
            label=best_label,
            confidence=confidence,
            explanation=f"Matched {hits} keyword(s) for '{best_label}'. Replace this stub with a real model.",
            sources=["Replace with the dataset(s) your model was trained on"],
        )


_registry: dict[Sector, SmallModel] = {}


def get_model(sector: Sector) -> SmallModel:
    if sector not in _registry:
        _registry[sector] = StubModel(sector)
    return _registry[sector]
