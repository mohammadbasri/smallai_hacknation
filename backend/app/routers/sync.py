"""Store-and-forward endpoint.

The device saves records while offline and posts them here when a signal appears.
This in-memory store is a placeholder: swap in SQLite/Postgres or forward to DHIS2 etc.
"""
from fastapi import APIRouter

from app.schemas import SyncRequest, SyncResponse

router = APIRouter(prefix="/sync", tags=["sync"])

_STORE: dict[str, dict] = {}


@router.post("", response_model=SyncResponse)
def sync(req: SyncRequest) -> SyncResponse:
    accepted: list[str] = []
    rejected: dict[str, str] = {}
    for rec in req.records:
        if rec.id in _STORE:
            accepted.append(rec.id)  # idempotent: already have it
            continue
        _STORE[rec.id] = {"client_id": req.client_id, **rec.model_dump(mode="json")}
        accepted.append(rec.id)
    return SyncResponse(accepted=accepted, rejected=rejected)


@router.get("")
def list_synced():
    return {"count": len(_STORE), "records": list(_STORE.values())}
