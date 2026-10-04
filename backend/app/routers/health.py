from fastapi import APIRouter

from app.config import get_settings
from app.services import store
from app.services.model import get_hub

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    s = get_settings()
    hub = get_hub()
    return {
        "status": "ok",
        "app": s.app_name,
        "sector": "tourism",
        "default_language": s.default_language,
        "threshold": s.confidence_threshold,
        "models": [m["name"] + "@" + m["version"] for m in hub.summaries()],
        "sms_provider": s.sms_provider,
        "synced_records": store.sync_count(),
    }
