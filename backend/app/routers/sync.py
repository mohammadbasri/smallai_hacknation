"""Store-and-forward endpoint (SQLite-backed).

The phone saves records while offline and posts them here when a signal appears. Each record is idempotent on id
and is also applied to the matching table (enquiries, bookings, feedback, profile) so the edge box / dashboard
sees what happened on the phone.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.schemas import SyncRequest, SyncResponse
from app.services import store

log = logging.getLogger("karibu.sync")
router = APIRouter(prefix="/sync", tags=["sync"])


def _apply(rec: dict) -> None:
    kind, p, rid = rec["kind"], rec["payload"], rec["id"]
    now = store.now_iso()
    if kind == "enquiry":
        store.enquiry_upsert(
            {
                "id": rid, "created_at": p.get("created_at", now), "source": p.get("source", "app"),
                "visitor_contact": p.get("visitor_contact", ""), "text": p["text"], "language": p.get("language", "?"),
                "intent": p.get("intent"), "confidence": float(p.get("confidence", 0.0)), "decision": p.get("decision", "ask_a_person"),
                "reply_for_visitor": p.get("reply_for_visitor"), "status": p.get("status", "new"),
                "operator_action": p.get("operator_action"), "sent_text": p.get("sent_text"),
            }
        )
    elif kind == "booking":
        store.booking_upsert(
            {
                "id": rid, "created_at": p.get("created_at", now), "updated_at": p.get("updated_at", now),
                "visitor_name": p.get("visitor_name", ""), "visitor_contact": p.get("visitor_contact", ""),
                "language": p.get("language", "en"), "date": p["date"], "time": p.get("time", "09:00"),
                "party_size": int(p.get("party_size", 2)), "status": p.get("status", "pending"), "notes": p.get("notes", ""),
                "source": p.get("source", "app"), "enquiry_id": p.get("enquiry_id"),
            }
        )
    elif kind == "feedback":
        store.feedback_upsert(
            {
                "id": rid, "created_at": p.get("created_at", now), "source": p.get("source", "app"),
                "visitor_contact": p.get("visitor_contact", ""), "text": p["text"], "language": p.get("language", "?"),
                "clauses": p.get("clauses", []),
            }
        )
    elif kind == "profile":
        store.profile_set(p)


@router.post("", response_model=SyncResponse)
def sync(req: SyncRequest) -> SyncResponse:
    accepted: list[str] = []
    rejected: dict[str, str] = {}
    for rec in req.records:
        d = rec.model_dump(mode="json")
        if store.sync_exists(rec.id):
            accepted.append(rec.id)  # idempotent: already have it
            continue
        try:
            _apply(d)
            store.sync_insert(req.client_id, d)
            accepted.append(rec.id)
        except Exception as exc:  # keep the record on the phone, tell it why
            log.warning("sync rejected %s: %s", rec.id, exc)
            rejected[rec.id] = str(exc)
    return SyncResponse(accepted=accepted, rejected=rejected)


@router.get("")
def list_synced():
    return {"count": store.sync_count(), "records": store.sync_list()}
