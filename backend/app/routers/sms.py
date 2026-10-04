"""SMS channel: the path that reaches Noor's BASIC phone.

Visitor -> service number -> /sms/inbound -> model -> SMS to Noor in Kiswahili with numbered options
Noor replies "1" / "2" / free text -> /sms/operator -> fixed reply (or her own words) -> visitor

Webhook formats accepted: Africa's Talking (form: from, to, text), Twilio (form: From, To, Body), or JSON {from, text}.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas import Decision
from app.services import store
from app.services.model import get_hub
from app.services.replies import get_templates
from app.services.sms import deliver_to_visitor, notify_operator

router = APIRouter(prefix="/sms", tags=["sms"])


async def _parse(request: Request) -> tuple[str, str]:
    ctype = request.headers.get("content-type", "")
    if "json" in ctype:
        body = await request.json()
        return str(body.get("from") or body.get("From") or body.get("sender") or ""), str(body.get("text") or body.get("Body") or "")
    form = await request.form()
    return str(form.get("from") or form.get("From") or ""), str(form.get("text") or form.get("Body") or "")


def _excerpt(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


@router.post("/inbound")
async def inbound(request: Request):
    """A visitor texted the farm's number."""
    sender, text = await _parse(request)
    if not text.strip():
        return {"ok": False, "reason": "empty message"}
    s = get_settings()
    hub = get_hub()
    t = get_templates()
    store.sms_log("in", sender, text, "?", "visitor_inbound")

    a = hub.analyse_enquiry(text, s.default_language)
    enquiry_id = str(uuid.uuid4())
    store.enquiry_upsert(
        {
            "id": enquiry_id, "created_at": store.now_iso(), "source": "sms", "visitor_contact": sender, "text": text,
            "language": a.language, "intent": a.intent, "confidence": a.confidence, "decision": a.decision.value,
            "reply_for_visitor": a.reply_for_visitor, "status": "new",
        }
    )
    lang_label = t.label("languages", a.language, s.default_language)
    if a.decision is Decision.answer and a.intent:
        msg = t.sms("new_enquiry", s.default_language, contact=sender, language=lang_label,
                    intent_label=t.label("intents", a.intent, s.default_language), excerpt=_excerpt(text))
    else:
        msg = t.sms("unsure_enquiry", s.default_language, contact=sender, language=lang_label,
                    pct=round(a.confidence * 100), excerpt=_excerpt(text))
    notification = notify_operator(msg, "operator_notification")
    return {"ok": True, "enquiry_id": enquiry_id, "analysis": a, "operator_sms": notification}


@router.post("/operator")
async def operator(request: Request):
    """Noor replied from her basic phone: '1' standard reply, '2' holding reply, anything else = her own words."""
    sender, text = await _parse(request)
    s = get_settings()
    t = get_templates()
    store.sms_log("in", sender or s.sms_operator_number, text, s.default_language, "operator_inbound")
    e = store.enquiry_latest_open_for()
    if not e:
        return {"ok": False, "operator_sms": notify_operator(t.sms("nothing_pending", s.default_language), "operator_notification")}

    choice = text.strip()
    if choice == "1" and e["decision"] == Decision.answer.value and e["reply_for_visitor"]:
        reply, action = e["reply_for_visitor"], "send_standard"
    elif choice in ("1", "2"):
        reply, action = get_hub().analyse_enquiry(e["text"]).holding_reply, "send_holding"
    else:
        reply, action = choice, "send_custom"

    delivery = deliver_to_visitor(e["visitor_contact"], reply, e["language"], f"reply:{action}")
    store.enquiry_update(e["id"], status="handled", operator_action=action, sent_text=reply)
    ack = notify_operator(t.sms("sent_ok", s.default_language, contact=e["visitor_contact"]), "operator_ack")
    return {"ok": True, "enquiry_id": e["id"], "operator_action": action, "sent_text": reply, "delivery": delivery, "operator_sms": ack}


@router.get("/outbox")
def outbox(limit: int = 100):
    """Everything the channel sent or received (the dashboard's SMS simulator reads this)."""
    s = get_settings()
    return {"provider": s.sms_provider, "operator_number": s.sms_operator_number, "service_number": s.sms_service_number,
            "messages": store.sms_list(limit)}
