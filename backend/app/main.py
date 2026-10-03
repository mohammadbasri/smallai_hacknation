from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import datasets, health, inference, sync

settings = get_settings()

app = FastAPI(
    title="Small AI for Development - API",
    description=(
        "Boilerplate backend for the Hack-Nation x World Bank Small AI hackathon. "
        "The device does the core work offline; this API handles sync, model updates "
        "and anything that genuinely needs a server."
    ),
    version="0.1.0",
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
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(inference.router, prefix=API_PREFIX)
app.include_router(sync.router, prefix=API_PREFIX)
app.include_router(datasets.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "Small AI backend running. See /docs for the OpenAPI UI."}
