"""Booking ledger. Not AI; it is the workflow the AI feeds. Messages to visitors are fixed templates."""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.schemas import Booking, BookingIn, BookingPatch
from app.services import store
from app.services.replies import current_profile, get_templates
from app.services.sms import deliver_to_visitor

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[Booking])
def list_bookings(status: str | None = None) -> list[Booking]:
    return [Booking(**b) for b in store.booking_list(status)]


@router.post("", response_model=Booking)
def create(b: BookingIn) -> Booking:
    now = store.now_iso()
    row = {**b.model_dump(), "id": b.id or str(uuid.uuid4()), "created_at": now, "updated_at": now}
    return Booking(**store.booking_upsert(row))


@router.patch("/{booking_id}", response_model=Booking)
def patch(booking_id: str, p: BookingPatch) -> Booking:
    row = store.booking_patch(booking_id, p.model_dump())
    if not row:
        raise HTTPException(404, "booking not found")
    return Booking(**row)


@router.get("/{booking_id}/message")
def message(booking_id: str, kind: Literal["booking_confirmed", "booking_reminder", "booking_cancelled", "followup"] = "booking_confirmed",
            lang: str | None = None):
    """Render the fixed template for this booking in the visitor's language. Noor sends it; the tool only drafts."""
    b = store.booking_get(booking_id)
    if not b:
        raise HTTPException(404, "booking not found")
    t = get_templates()
    text = t.special(kind, lang or b["language"], current_profile(), date=b["date"], time=b["time"], party_size=b["party_size"])
    return {"booking_id": booking_id, "kind": kind, "language": lang or b["language"], "text": text}


@router.post("/{booking_id}/send")
def send(booking_id: str, kind: Literal["booking_confirmed", "booking_reminder", "booking_cancelled", "followup"] = "booking_confirmed"):
    b = store.booking_get(booking_id)
    if not b:
        raise HTTPException(404, "booking not found")
    if not b.get("visitor_contact"):
        raise HTTPException(400, "booking has no visitor contact")
    text = message(booking_id, kind)["text"]
    delivery = deliver_to_visitor(b["visitor_contact"], text, b["language"], kind)
    return {"booking_id": booking_id, "kind": kind, "text": text, "delivery": delivery}
