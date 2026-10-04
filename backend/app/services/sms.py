"""SMS gateway. Default provider "console" only records messages in the outbox (the dashboard shows them).

Africa's Talking and Twilio are wired behind the same function so the demo flow is identical to production.
The edge box (Raspberry Pi / laptop at the cooperative) runs this; Noor's basic phone only needs SMS.
"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.services import store

log = logging.getLogger("karibu.sms")


def _send_real(to: str, text: str) -> str:
    s = get_settings()
    try:
        import httpx  # optional at runtime; listed in requirements
    except ImportError:  # pragma: no cover
        return "httpx not installed; message logged only"
    try:
        if s.sms_provider == "africastalking" and s.at_username and s.at_api_key:
            r = httpx.post(
                "https://api.africastalking.com/version1/messaging",
                headers={"apiKey": s.at_api_key, "Accept": "application/json"},
                data={"username": s.at_username, "to": to, "message": text, **({"from": s.at_sender_id} if s.at_sender_id else {})},
                timeout=15,
            )
            return f"africastalking {r.status_code}"
        if s.sms_provider == "twilio" and s.twilio_account_sid and s.twilio_auth_token:
            r = httpx.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{s.twilio_account_sid}/Messages.json",
                auth=(s.twilio_account_sid, s.twilio_auth_token),
                data={"To": to, "From": s.sms_service_number, "Body": text},
                timeout=15,
            )
            return f"twilio {r.status_code}"
    except Exception as exc:  # network failure must never crash the webhook
        log.warning("SMS send failed: %s", exc)
        return f"send failed: {exc}"
    return "provider not configured; message logged only"


def send_sms(to: str, text: str, language: str, purpose: str) -> dict:
    """Log in the outbox and, if a real provider is configured, send. Returns the outbox row plus delivery note."""
    row = store.sms_log("out", to, text, language, purpose)
    s = get_settings()
    note = "console" if s.sms_provider == "console" else _send_real(to, text)
    return {**row, "delivery": note}


def deliver_to_visitor(contact: str, text: str, language: str, purpose: str) -> dict:
    return send_sms(contact, text, language, purpose)


def notify_operator(text: str, purpose: str) -> dict:
    s = get_settings()
    return send_sms(s.sms_operator_number, text, s.default_language, purpose)
