"""Fixed-template rendering. Every visitor-facing sentence the tool can produce lives in shared/templates/*.json.

No free-text generation: this is how the entry satisfies the brief's "fixed list of answers" guidance and keeps
hallucination structurally impossible. Slots are filled from the operator profile; a missing slot renders empty
rather than raising, so a half-filled profile still produces a usable (if terse) message.
"""
from __future__ import annotations

import json
import string
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.schemas import Profile
from app.services import store


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


class Templates:
    def __init__(self, shared_dir: Path):
        t = shared_dir / "templates"
        self.replies = json.loads((t / "replies.json").read_text(encoding="utf-8"))
        self.labels = json.loads((t / "labels.json").read_text(encoding="utf-8"))
        self.listing = json.loads((t / "listing.json").read_text(encoding="utf-8"))
        self.version = self.replies.get("version", "0")
        self.visitor_languages: list[str] = self.replies["languages"]

    # ----------------------------------------------------------------- rendering
    @staticmethod
    def render(template: str, values: dict) -> str:
        return string.Formatter().vformat(template, (), _SafeDict({k: ("" if v is None else v) for k, v in values.items()}))

    def _lang(self, lang: str | None) -> str:
        return lang if lang in self.visitor_languages else "en"

    def reply_for_intent(self, intent: str, lang: str, profile: dict) -> str | None:
        block = self.replies["intents"].get(intent)
        if not block:
            return None
        return self.render(block[self._lang(lang)], profile)

    def special(self, name: str, lang: str, profile: dict, **extra) -> str:
        block = self.replies["special"][name]
        return self.render(block[self._lang(lang)], {**profile, **extra})

    def listing_text(self, lang: str, profile: dict) -> str:
        return self.render(self.listing["listing"][self._lang(lang)], profile)

    # ----------------------------------------------------------------- operator-facing
    def _op(self, lang: str) -> str:
        return lang if lang in ("en", "sw") else "en"

    def label(self, kind: str, key: str, operator_lang: str) -> str:
        block = self.labels.get(kind, {}).get(key)
        if not block:
            return key.replace("_", " ")
        return block.get(self._op(operator_lang), block["en"])

    def operator_summary(self, kind: str, operator_lang: str, **values) -> str:
        block = self.labels["operator_summary"][kind]
        return self.render(block[self._op(operator_lang)], values)

    def sms(self, kind: str, operator_lang: str, **values) -> str:
        block = self.labels["sms"][kind]
        return self.render(block[self._op(operator_lang)], values)

    def all_visitor_texts(self) -> dict:
        """The complete, auditable list of things the tool may say to a visitor."""
        return {"intents": self.replies["intents"], "special": self.replies["special"]}


@lru_cache
def _templates_for(shared_dir: str) -> Templates:
    return Templates(Path(shared_dir))


def get_templates() -> Templates:
    return _templates_for(get_settings().shared_dir)


def current_profile() -> dict:
    """Operator profile from the DB, falling back to the fictional Noor defaults."""
    saved = store.profile_get()
    base = Profile().model_dump()
    if saved:
        base.update({k: v for k, v in saved.items() if k in base})
    return base
