"""Python side of the cross-runtime parity check. Prints the same JSON structure as frontend/scripts/parity.mjs.

    cd backend && .venv/Scripts/python -m ml.parity
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services.tinymodel import TinyModel, split_clauses

ROOT = Path(__file__).resolve().parents[2]


def compute() -> dict:
    probes = json.loads((ROOT / "backend" / "ml" / "parity_probes.json").read_text(encoding="utf-8"))
    result: dict = {"models": {}, "clauses": {}}
    for name in ("intent", "langid", "aspect", "sentiment"):
        m = TinyModel.load(ROOT / "shared" / "models" / f"{name}.json")
        rows = []
        for s in probes["sentences"]:
            label, conf, _ = m.predict(s)
            rows.append({"text": s, "label": label, "confidence": round(conf, 6)})
        result["models"][name] = rows
    for r in probes["reviews"]:
        result["clauses"][r] = split_clauses(r)
    return result


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False))
