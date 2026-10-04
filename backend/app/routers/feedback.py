"""Visitor feedback: analyse clause by clause, store, and aggregate into 'keep doing' / 'fix next'."""
from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import APIRouter

from app.schemas import AspectSummary, FeedbackAnalysis, FeedbackRequest, FeedbackSummary
from app.services import store
from app.services.model import get_hub

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackAnalysis)
def add_feedback(req: FeedbackRequest) -> FeedbackAnalysis:
    hub = get_hub()
    lang, clauses = hub.analyse_feedback(req.text, req.language)
    fid = str(uuid.uuid4())
    store.feedback_upsert(
        {
            "id": fid,
            "created_at": store.now_iso(),
            "source": req.source,
            "visitor_contact": req.visitor_contact or "",
            "text": req.text,
            "language": lang,
            "clauses": [c.model_dump(mode="json") for c in clauses],
        }
    )
    confident = sum(1 for c in clauses if c.aspect and c.sentiment)
    return FeedbackAnalysis(
        id=fid, language=lang, clauses=clauses, n_confident=confident, n_unsure=len(clauses) - confident,
        model_name=hub.name, model_version=hub.version,
    )


@router.get("")
def list_feedback(limit: int = 200):
    return {"feedback": store.feedback_list(limit)}


def summarise(reviews: list[dict], aspects: list[str]) -> FeedbackSummary:
    pos: dict[str, list[str]] = defaultdict(list)
    neg: dict[str, list[str]] = defaultdict(list)
    n_clauses = n_conf = 0
    for r in reviews:
        for c in r["clauses"]:
            n_clauses += 1
            if c.get("aspect") and c.get("sentiment"):
                n_conf += 1
                (pos if c["sentiment"] == "positive" else neg)[c["aspect"]].append(c["text"])
    rows = [
        AspectSummary(aspect=a, positive=len(pos[a]), negative=len(neg[a]),
                      examples_positive=pos[a][:3], examples_negative=neg[a][:3])
        for a in aspects if a != "other"
    ]
    keep = sorted([r for r in rows if r.positive > r.negative], key=lambda r: -(r.positive - r.negative))[:3]
    fix = sorted([r for r in rows if r.negative > 0], key=lambda r: -r.negative)[:3]
    return FeedbackSummary(
        n_reviews=len(reviews), n_clauses=n_clauses, n_confident=n_conf, n_unsure=n_clauses - n_conf,
        keep_doing=keep, fix_next=fix, aspects=rows,
    )


@router.get("/summary", response_model=FeedbackSummary)
def summary() -> FeedbackSummary:
    """What visitors keep praising and what they wish were different. Only confident clauses count;
    the unsure count is shown so Noor knows how much the tool skipped."""
    return summarise(store.feedback_list(), get_hub().labels("aspect"))
