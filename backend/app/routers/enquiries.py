"""Enquiry inbox: analyse + store, and record what Noor decided to do with each message."""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas import Decision, EnquiryAnalysis, EnquiryRequest
from app.services import store
from app.services.model import get_hub
from app.services.sms import deliver_to_visitor

router = APIRouter(prefix="/enquiries", tags=["enquiries"])


class EnquiryCreate(EnquiryRequest):
    visitor_contact: str = ""
    source: str = "app"
    id: str | None = None


class EnquiryStored(BaseModel):
    id: str
    analysis: EnquiryAnalysis


class EnquiryAction(BaseModel):
    action: Literal["send_standard", "send_holding", "send_custom", "dismiss"]
    text: str | None = Field(None, description="Required for send_custom: Noor's own reply")


@router.post("", response_model=EnquiryStored)
def create(req: EnquiryCreate) -> EnquiryStored:
    analysis = get_hub().analyse_enquiry(req.text, req.operator_language)
    enquiry_id = req.id or str(uuid.uuid4())
    store.enquiry_upsert(
        {
            "id": enquiry_id,
            "created_at": store.now_iso(),
            "source": req.source,
            "visitor_contact": req.visitor_contact,
            "text": req.text,
            "language": analysis.language,
            "intent": analysis.intent,
            "confidence": analysis.confidence,
            "decision": analysis.decision.value,
            "reply_for_visitor": analysis.reply_for_visitor,
            "status": "new",
        }
    )
    return EnquiryStored(id=enquiry_id, analysis=analysis)


@router.get("")
def list_enquiries(limit: int = 100):
    return {"enquiries": store.enquiry_list(limit)}


@router.post("/{enquiry_id}/action")
def act(enquiry_id: str, action: EnquiryAction):
    """Noor's decision. This is the human-in-the-loop step: nothing reaches a visitor without it."""
    e = store.enquiry_get(enquiry_id)
    if not e:
        raise HTTPException(404, "enquiry not found")
    text: str | None = None
    if action.action == "send_standard":
        if e["decision"] != Decision.answer.value or not e["reply_for_visitor"]:
            raise HTTPException(400, "no standard reply available for this enquiry; send holding or custom")
        text = e["reply_for_visitor"]
    elif action.action == "send_holding":
        analysis = get_hub().analyse_enquiry(e["text"])
        text = analysis.holding_reply
    elif action.action == "send_custom":
        if not action.text or not action.text.strip():
            raise HTTPException(400, "text is required for send_custom")
        text = action.text.strip()

    delivered = None
    if text and e.get("visitor_contact"):
        delivered = deliver_to_visitor(e["visitor_contact"], text, e["language"], f"reply:{action.action}")
    store.enquiry_update(enquiry_id, status="handled", operator_action=action.action, sent_text=text)
    return {"id": enquiry_id, "status": "handled", "operator_action": action.action, "sent_text": text, "delivery": delivered}
