"""Karibu: Small AI for a small tourism operator (Hack-Nation x World Bank, Small AI for Development 2026).

Routes (all under /api): health, inference, enquiries, feedback, bookings, profile, sms, sync, datasets.
The built frontend and the shared model/template artifacts are served from this same process in production
so the whole tool is one container that also runs on an edge box (D-004, D-005).
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import bookings, datasets, enquiries, feedback, health, inference, profile, sms, sync

settings = get_settings()

app = FastAPI(
    title="Karibu · Small AI for a farm-tour operator",
    description=(
        "Reads visitor messages (en/fr/sw), tells Noor what they want in Kiswahili, drafts a fixed-template reply "
        "she approves, and turns visitor feedback into 'keep doing / fix next'. Works over SMS for a basic phone "
        "and offline in the browser for a smartphone. A person makes every final call."
    ),
    version="1.0.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
for r in (health, inference, enquiries, feedback, bookings, profile, sms, sync, datasets):
    app.include_router(r.router, prefix=API_PREFIX)

# Shared artifacts (models + templates) at /shared so the browser can fetch and cache them from the same origin.
shared = settings.shared_path
if shared.is_dir():
    app.mount("/shared", StaticFiles(directory=str(shared)), name="shared")

# Built frontend (single-container deployment). Falls back to a JSON hello when not built.
static = Path(settings.static_dir)
if static.is_dir() and (static / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(static / "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = static / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(static / "index.html")

else:

    @app.get("/")
    def root():
        return {"message": "Karibu backend running. See /docs for the OpenAPI UI. Build the frontend to serve it from here."}
