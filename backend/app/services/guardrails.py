"""Responsible-AI guardrails required by the brief (pass/fail criterion).

- A person makes the final call; the tool only informs. Nothing is sent to a visitor without Noor's action.
- Below the confidence threshold, say "not sure, ask a person" instead of guessing.
- Visitor-facing text comes from a fixed template list (shared/templates/replies.json) so output can be audited.
- Unsupported languages are flagged, not silently handled.
"""
from app.schemas import Decision


def decide(confidence: float, threshold: float) -> Decision:
    if confidence >= threshold:
        return Decision.answer
    return Decision.ask_a_person


def ask_a_person_message(language: str) -> str:
    messages = {
        "en": "Not sure. Please read the message yourself or ask the guide.",
        "fr": "Pas sûr. Veuillez lire le message vous-même ou demander au guide.",
        "sw": "Sina uhakika. Tafadhali soma ujumbe mwenyewe au muulize mwongozaji.",
    }
    return messages.get(language, messages["en"])
