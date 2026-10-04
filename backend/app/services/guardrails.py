"""Responsible-AI guardrails required by the brief (pass/fail criterion).

- A person makes the final call; the tool only informs.
- Below the confidence threshold, say "not sure, ask a person" instead of guessing.
- Answers come from a fixed list so output can be audited.
"""
from app.schemas import Decision


def decide(confidence: float, threshold: float) -> Decision:
    if confidence >= threshold:
        return Decision.answer
    return Decision.ask_a_person


def ask_a_person_message(language: str) -> str:
    messages = {
        "en": "Not sure. Please ask a person (a tour guide or tourism officer).",
        "sw": "Sina uhakika. Tafadhali muulize mtu (kiongozi wa watalii au afisa utalii).",
    }
    return messages.get(language, messages["en"])
