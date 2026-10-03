from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas import Decision, InferenceRequest, InferenceResponse, Sector
from app.services import guardrails
from app.services.model import get_model

router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("", response_model=InferenceResponse)
def infer(req: InferenceRequest, settings: Settings = Depends(get_settings)) -> InferenceResponse:
    model = get_model(req.sector)
    pred = model.predict(req.text, req.language)
    decision = guardrails.decide(pred.confidence, settings.confidence_threshold)

    explanation = pred.explanation
    label = pred.label
    if decision is Decision.ask_a_person:
        explanation = guardrails.ask_a_person_message(req.language)
        label = None

    return InferenceResponse(
        decision=decision,
        label=label,
        confidence=pred.confidence,
        explanation=explanation,
        language=req.language,
        model_name=model.name,
        model_version=model.version,
        sources=pred.sources,
    )


@router.get("/labels/{sector}")
def labels(sector: Sector):
    """The fixed list of answers the tool is allowed to give for a sector."""
    model = get_model(sector)
    return {"sector": sector, "labels": model.labels}
