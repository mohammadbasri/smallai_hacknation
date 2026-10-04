"""The browser runtime (TypeScript) and the server runtime (Python) must agree on every prediction.
Skipped when Node is not available (CI without a frontend toolchain)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ml.parity import compute

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(shutil.which("node") is None or not (ROOT / "frontend" / "node_modules").exists(), reason="node toolchain not available")
def test_typescript_and_python_runtimes_agree():
    js = subprocess.run(["node", "scripts/parity.mjs"], cwd=ROOT / "frontend", capture_output=True, text=True, encoding="utf-8", shell=True)
    assert js.returncode == 0, js.stderr
    ts_out = json.loads(js.stdout.strip().splitlines()[-1])
    py_out = compute()

    assert ts_out["clauses"] == py_out["clauses"], "clause splitting differs"
    for name, py_rows in py_out["models"].items():
        for py_row, ts_row in zip(py_rows, ts_out["models"][name]):
            assert py_row["text"] == ts_row["text"]
            assert py_row["label"] == ts_row["label"], f"{name}: {py_row['text']!r} -> py {py_row['label']} vs ts {ts_row['label']}"
            assert abs(py_row["confidence"] - ts_row["confidence"]) < 1e-4, f"{name}: {py_row['text']!r}"
