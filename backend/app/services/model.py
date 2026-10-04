"""Model hub: loads the four tiny models from shared/models and exposes the two analyses the tool performs.

The same JSON artifacts run in the browser (frontend/src/lib/tinyModel.ts); this Python side serves the SMS channel
(basic phones) and the API. Both sides apply the same threshold and the same fixed templates.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.schemas import ClauseAnalysis, Decision, EnquiryAnalysis, Ranked
from app.services import guardrails
from app.services.replies import current_profile, get_templates
from app.services.tinymodel import TinyModel, split_clauses

SUPPORTED_VISITOR_LANGUAGES = ("en", "fr", "sw")


class ModelHub:
    name = "karibu-tiny-linear"

    def __init__(self, shared_dir: Path, threshold: float):
        models = shared_dir / "models"
        self.intent = TinyModel.load(models / "intent.json")
        self.langid = TinyModel.load(models / "langid.json")
        self.aspect = TinyModel.load(models / "aspect.json")
        self.sentiment = TinyModel.load(models / "sentiment.json")
        self.threshold = threshold
        self.version = self.intent.version

    # ----------------------------------------------------------------- enquiries
    def detect_language(self, text: str) -> tuple[str, float]:
        lang, conf, _ = self.langid.predict(text)
        return lang, conf

    def analyse_enquiry(self, text: str, operator_language: str = "sw") -> EnquiryAnalysis:
        t = get_templates()
        profile = current_profile()

        lang, lang_conf = self.detect_language(text)
        # Three cases: supported language (answer in it); confidently another language (send the fixed
        # 'please write in en/fr/sw' note); unsure what language (defer to Noor, no suggested reply).
        supported = lang in SUPPORTED_VISITOR_LANGUAGES and lang_conf >= self.threshold
        other_language = lang == "other" and lang_conf >= self.threshold
        reply_lang = lang if supported else "en"

        intent, conf, ranked = self.intent.predict(text)
        decision = guardrails.decide(conf, self.threshold)
        if intent == "other":
            decision = Decision.ask_a_person  # "other" is never answered automatically

        reply_visitor = reply_operator = None
        if other_language:
            summary = t.operator_summary("unsupported_language", operator_language)
            reply_visitor = t.special("unsupported_language", "en", profile)
            reply_operator = t.special("unsupported_language", operator_language, profile)
            decision = Decision.ask_a_person
        elif not supported:
            decision = Decision.ask_a_person
            summary = t.operator_summary("ask_a_person", operator_language, pct=round(min(conf, lang_conf) * 100))
        elif decision is Decision.answer:
            reply_visitor = t.reply_for_intent(intent, reply_lang, profile)
            reply_operator = t.reply_for_intent(intent, operator_language, profile)
            summary = t.operator_summary(
                "answer", operator_language,
                language=t.label("languages", lang, operator_language),
                intent_label=t.label("intents", intent, operator_language),
            )
        else:
            summary = t.operator_summary("ask_a_person", operator_language, pct=round(conf * 100))

        return EnquiryAnalysis(
            decision=decision,
            language=lang,
            language_confidence=round(lang_conf, 4),
            language_supported=supported,
            intent=intent if decision is Decision.answer else None,
            confidence=round(conf, 4),
            ranked=[Ranked(label=l, probability=round(p, 4)) for l, p in ranked],
            reply_for_visitor=reply_visitor,
            reply_for_operator=reply_operator,
            operator_summary=summary,
            holding_reply=t.special("holding", reply_lang, profile),
            model_name=self.name,
            model_version=self.version,
        )

    # ----------------------------------------------------------------- feedback
    def analyse_feedback(self, text: str, language: str | None = None) -> tuple[str, list[ClauseAnalysis]]:
        lang = language or self.detect_language(text)[0]
        clauses: list[ClauseAnalysis] = []
        for clause in split_clauses(text):
            asp, asp_conf, _ = self.aspect.predict(clause)
            sen, sen_conf, _ = self.sentiment.predict(clause)
            asp_dec = guardrails.decide(asp_conf, self.threshold)
            sen_dec = guardrails.decide(sen_conf, self.threshold)
            clauses.append(
                ClauseAnalysis(
                    text=clause,
                    aspect=asp if asp_dec is Decision.answer else None,
                    aspect_confidence=round(asp_conf, 4),
                    aspect_decision=asp_dec,
                    sentiment=sen if sen_dec is Decision.answer else None,
                    sentiment_confidence=round(sen_conf, 4),
                    sentiment_decision=sen_dec,
                )
            )
        return lang, clauses

    # ----------------------------------------------------------------- meta
    def summaries(self) -> list[dict]:
        return [m.summary() for m in (self.intent, self.langid, self.aspect, self.sentiment)]

    def labels(self, model: str) -> list[str]:
        return {"intent": self.intent, "langid": self.langid, "aspect": self.aspect, "sentiment": self.sentiment}[model].classes


@lru_cache
def _hub_for(shared_dir: str, threshold: float) -> ModelHub:
    return ModelHub(Path(shared_dir), threshold)


def get_hub() -> ModelHub:
    s = get_settings()
    return _hub_for(s.shared_dir, s.confidence_threshold)
