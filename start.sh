#!/usr/bin/env bash
# Small AI for Development - install anything missing, then run backend + frontend (macOS / Linux)
#
# Usage:  ./start.sh            install anything missing, then run both servers
#         ./start.sh setup      install only, do not start the servers
set -euo pipefail
cd "$(dirname "$0")"

SETUP_ONLY=""
[[ "${1:-}" == "setup" ]] && SETUP_ONLY=1

echo
echo "=== Small AI for Development (macOS / Linux) ==="
echo

# ---------- Locate Python 3.11+ ----------
PY=""
for candidate in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
     && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$candidate"
    break
  fi
done
if [[ -z "$PY" ]]; then
  echo "[ERROR] Python 3.11 or newer was not found."
  echo "        macOS: brew install python@3.11   (or https://www.python.org/downloads/)"
  exit 1
fi
echo "Using Python: $PY ($("$PY" --version))"

# ---------- Locate Node.js / npm ----------
if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] Node.js / npm was not found."
  echo "        macOS: brew install node   (or https://nodejs.org/)"
  exit 1
fi
echo "Using Node:   $(node --version)"

# ---------- Backend ----------
echo
echo "[1/3] Backend: virtual environment + Python packages"
if [[ ! -x backend/.venv/bin/python ]]; then
  "$PY" -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install --upgrade pip --quiet
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt --quiet

echo
echo "[2/3] Backend: .env file"
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "      Created backend/.env from .env.example"
else
  echo "      backend/.env already exists, leaving it alone"
fi

# ---------- Frontend ----------
echo
echo "[3/3] Frontend: npm packages"
( cd frontend && npm install --no-audit --no-fund )

echo
echo "=== Setup complete ==="
[[ -n "$SETUP_ONLY" ]] && exit 0

# ---------- Run ----------
echo
echo "=== Starting Small AI for Development ==="
echo "  Backend  : http://localhost:8000   (OpenAPI UI: http://localhost:8000/docs)"
echo "  Frontend : http://localhost:5173"
echo
echo "Press Ctrl+C to stop both servers."
echo

cleanup() {
  echo
  echo "Stopping servers..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

( cd backend && exec .venv/bin/python -m uvicorn app.main:app --reload --port 8000 ) &
BACKEND_PID=$!

( cd frontend && exec npm run dev ) &
FRONTEND_PID=$!

# Give Vite a moment to bind the port, then open the browser.
sleep 4
if command -v open >/dev/null 2>&1; then
  open http://localhost:5173
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:5173 >/dev/null 2>&1 || true
fi

wait
