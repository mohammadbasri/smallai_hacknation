"""Operator profile: the facts every reply template is filled from, and the generated listing text."""
from fastapi import APIRouter

from app.schemas import Profile
from app.services import store
from app.services.replies import current_profile, get_templates

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Profile)
def get_profile() -> Profile:
    return Profile(**current_profile())


@router.put("", response_model=Profile)
def put_profile(p: Profile) -> Profile:
    store.profile_set(p.model_dump())
    return p


@router.get("/listing")
def listing(lang: str = "en"):
    """Discoverability: listing text built from the profile only, in en/fr/sw."""
    return {"language": lang, "text": get_templates().listing_text(lang, current_profile())}
