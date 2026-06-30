"""The questionnaire structure and the Brief it produces.

`QUESTIONS` is structural only — ids, types, and stable *value keys* for choice
options. All human-readable text (labels, placeholders, option labels) lives in
`i18n.py`, keyed by these ids/values. The frontend renders a localized form via
`i18n.localized_questions`; answers come back as value keys, so backend logic is
language-independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import i18n

# Structural schema. `options` are stable value keys; labels are in i18n.OPTIONS.
QUESTIONS: list[dict[str, Any]] = [
    {"id": "name", "type": "text", "required": True},
    {"id": "tagline", "type": "text", "required": False},
    {"id": "industry", "type": "textarea", "required": True},
    {
        "id": "pages", "type": "multiselect", "required": True,
        "options": ["home", "about", "services", "portfolio", "pricing", "contact"],
        "default": ["home", "about", "services", "contact"],
    },
    {
        "id": "style", "type": "select", "required": True,
        "options": ["modern", "bold", "elegant", "surprise"],
        "default": "surprise",
    },
    {
        "id": "tone", "type": "select", "required": True,
        "options": ["friendly", "professional", "luxury", "playful"],
        "default": "friendly",
    },
    {"id": "color", "type": "color", "required": False, "default": ""},
    {"id": "cta", "type": "text", "required": False},
    {"id": "services", "type": "textarea", "required": False},
]

_BY_ID = {q["id"]: q for q in QUESTIONS}


@dataclass
class Brief:
    """Normalized, validated answers (all choices as stable value keys)."""

    name: str
    industry: str
    pages: list[str]            # value keys: "home", "about", …
    style: str                  # "modern" | "bold" | "elegant" | "surprise"
    tone: str                   # "friendly" | "professional" | "luxury" | "playful"
    lang: str = "en"
    tagline: str = ""
    color: str = ""
    cta: str = ""
    services: list[str] = field(default_factory=list)

    @classmethod
    def from_answers(cls, answers: dict[str, Any]) -> "Brief":
        """Build a Brief from raw answers; errors are reported in the answer language."""
        lang = i18n.norm_lang(answers.get("lang"))

        errors = []
        for q in QUESTIONS:
            if q.get("required") and not answers.get(q["id"]):
                errors.append(i18n.question_label(q["id"], lang))
        if errors:
            joiner = ", "
            prefix = "Bitte ausfüllen: " if lang == "de" else "Please fill in: "
            raise ValueError(prefix + joiner.join(errors))

        pages = answers.get("pages") or _BY_ID["pages"]["default"]
        if isinstance(pages, str):
            pages = [pages]
        # Home is always present and always first.
        pages = ["home"] + [p for p in pages if p != "home"]

        services_raw = (answers.get("services") or "").strip()
        services = [s.strip() for s in services_raw.splitlines() if s.strip()]

        cta = (answers.get("cta") or "").strip() or i18n.site(lang)["default_cta"]

        return cls(
            name=answers["name"].strip(),
            industry=answers["industry"].strip(),
            pages=pages,
            style=answers.get("style") or _BY_ID["style"]["default"],
            tone=answers.get("tone") or _BY_ID["tone"]["default"],
            lang=lang,
            tagline=(answers.get("tagline") or "").strip(),
            color=(answers.get("color") or "").strip(),
            cta=cta,
            services=services,
        )
