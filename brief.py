"""The questionnaire structure and the Brief it produces.

`QUESTIONS` is structural only — ids, types, groups, and stable *value keys* for
choice options. All human-readable text (labels, option labels, group names)
lives in `i18n.py`, keyed by these ids/values. The frontend renders a localized
form via `i18n.localized_questions`; answers come back as value keys, so backend
logic is language-independent.

Questions are organized into three groups the wizard presents as parts:
  you      — about the person / business (asked first)
  website  — what the website should do (features)
  look     — the design

Almost every question is multiple choice (tap to answer) — kept deliberately
easy for non-technical customers. Only the business name and the optional
example link require typing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import i18n

QUESTIONS: list[dict[str, Any]] = [
    # 1) About you
    {"id": "name", "type": "text", "required": True, "group": "you"},
    {"id": "business_type", "type": "select", "required": True, "group": "you",
     "options": ["food", "shop", "trade", "health", "beauty", "professional", "other"]},
    {"id": "area", "type": "select", "required": True, "group": "you",
     "options": ["local", "region", "country", "online"]},
    {"id": "years", "type": "select", "required": False, "group": "you",
     "options": ["new", "few", "ten", "twentyfive"]},
    # 2) Your website
    {"id": "goal", "type": "select", "required": True, "group": "website",
     "options": ["calls", "bookings", "show", "sell", "visit"]},
    {"id": "pages", "type": "multiselect", "required": True, "group": "website",
     "options": ["home", "about", "services", "gallery", "pricing", "reviews", "contact"],
     "default": ["home", "about", "services", "contact"]},
    {"id": "features", "type": "multiselect", "required": False, "group": "website",
     "options": ["booking", "contactform", "map", "gallery", "reviews", "shop", "newsletter"],
     "default": []},
    # 3) The look
    {"id": "feel", "type": "select", "required": True, "group": "look",
     "options": ["warm", "professional", "modern", "classic"]},
    {"id": "colors", "type": "select", "required": True, "group": "look",
     "options": ["blue", "green", "warm", "elegant", "neutral", "designer"],
     "default": "designer"},
    {"id": "logo", "type": "select", "required": False, "group": "look",
     "options": ["have", "need", "unsure"]},
    {"id": "example", "type": "text", "required": False, "group": "look"},
]

_BY_ID = {q["id"]: q for q in QUESTIONS}


@dataclass
class Brief:
    """Normalized, validated answers (all choices as stable value keys)."""

    name: str
    business_type: str
    area: str
    goal: str
    pages: list[str]            # value keys: "home", "about", …
    feel: str
    colors: str
    lang: str = "en"
    years: str = ""
    features: list[str] = field(default_factory=list)
    logo: str = ""
    example: str = ""

    @classmethod
    def from_answers(cls, answers: dict[str, Any]) -> "Brief":
        """Build a Brief from raw answers; errors are reported in the answer language."""
        lang = i18n.norm_lang(answers.get("lang"))

        errors = []
        for q in QUESTIONS:
            if q.get("required") and not answers.get(q["id"]):
                errors.append(i18n.question_label(q["id"], lang))
        if errors:
            prefix = "Bitte ausfüllen: " if lang == "de" else "Please fill in: "
            raise ValueError(prefix + ", ".join(errors))

        def as_list(v, default):
            if not v:
                return list(default)
            return [v] if isinstance(v, str) else list(v)

        pages = as_list(answers.get("pages"), _BY_ID["pages"]["default"])
        pages = ["home"] + [p for p in pages if p != "home"]      # home always first
        features = as_list(answers.get("features"), [])

        return cls(
            name=answers["name"].strip(),
            business_type=answers.get("business_type", ""),
            area=answers.get("area", ""),
            goal=answers.get("goal", ""),
            pages=pages,
            feel=answers.get("feel", ""),
            colors=answers.get("colors") or "designer",
            lang=lang,
            years=answers.get("years", ""),
            features=features,
            logo=answers.get("logo", ""),
            example=(answers.get("example") or "").strip(),
        )
