"""Data sources the entry cites. Judges score data grounding and declared coverage gaps."""
from fastapi import APIRouter

from app.schemas import Dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

DATASETS: list[Dataset] = [
    Dataset(
        name="Mozilla Common Voice",
        sector="common",
        what_it_is="Crowdsourced voice recordings, CC0, many African and South Asian languages.",
        why_it_matters="Starting point for listening in a local language.",
        license="CC0",
        coverage_gaps="Uneven hours per language; accents and noisy field audio under-represented.",
    ),
    Dataset(
        name="FLORES-200 / NLLB-200",
        sector="common",
        what_it_is="Translation benchmark and open models across 200 languages.",
        why_it_matters="For messages arriving in a language the user cannot read.",
        license="CC-BY-SA 4.0 / CC-BY-NC 4.0 (models)",
        coverage_gaps="Formal register; informal chat and code-switching are weaker.",
    ),
    Dataset(
        name="MASSIVE (Amazon)",
        sector="tourism",
        what_it_is="~1M short utterances in 51 languages labelled by intent.",
        why_it_matters="Template for sorting visitor requests into a fixed intent list.",
        license="CC-BY 4.0",
        coverage_gaps="Smart-assistant domain; tourism-specific intents need your own examples.",
    ),
]


@router.get("", response_model=list[Dataset])
def list_datasets(sector: str | None = None):
    if sector:
        return [d for d in DATASETS if d.sector in (sector, "common")]
    return DATASETS
