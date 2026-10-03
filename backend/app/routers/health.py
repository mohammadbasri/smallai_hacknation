from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    s = get_settings()
    return {"status": "ok", "app": s.app_name, "default_language": s.default_language}
