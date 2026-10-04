"""Pure inference endpoints (no persistence). The app uses these when online for parity checks;
offline it runs the same models in the browser."""
from fastapi import APIRouter, HTTPException

from app.schemas import EnquiryAnalysis, EnquiryRequest, FeedbackAnalysis, FeedbackRequest
from app.services.model import get_hub
from app.services.replies import get_templates

router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("/enquiry", response_model=EnquiryAnalysis)
def analyse_enquiry(req: EnquiryRequest) -> EnquiryAnalysis:
    return get_hub().analyse_enquiry(req.text, req.operator_language)


@router.post("/feedback", response_model=FeedbackAnalysis)
def analyse_feedback(req: FeedbackRequest) -> FeedbackAnalysis:
    hub = get_hub()
    lang, clauses = hub.analyse_feedback(req.text, req.language)
    confident = sum(1 for c in clauses if c.aspect and c.sentiment)
    return FeedbackAnalysis(
        id="preview",
        language=lang,
        clauses=clauses,
        n_confident=confident,
        n_unsure=len(clauses) - confident,
        model_name=hub.name,
        model_version=hub.version,
    )


@router.get("/models")
def models():
    """What is loaded, how big it is, and how it scored on hold-out. Judges can check 'small' and 'honest' here."""
    hub = get_hub()
    return {"threshold": hub.threshold, "models": hub.summaries(), "templates_version": get_templates().version}


@router.get("/labels/{model}")
def labels(model: str):
    """The fixed list of answers a model may give."""
    try:
        return {"model": model, "labels": get_hub().labels(model)}
    except KeyError:
        raise HTTPException(404, f"unknown model '{model}'")


@router.get("/replies")
def replies():
    """The complete, auditable set of visitor-facing texts (templates with slots)."""
    return get_templates().all_visitor_texts()
