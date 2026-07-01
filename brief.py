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

Almost every question is tap-to-answer (single- or multi-choice) — kept
deliberately easy for non-technical customers. Only the business name and two
optional free-text fields (what you offer, an example link) involve typing.

The answers are the raw material for the (separate) website-generation prompt,
so the set leans toward what actually specifies a site: what the business does,
who it serves, what makes it special, what the site must achieve, and the look.
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
    {"id": "offerings", "type": "textarea", "required": False, "group": "you"},
    {"id": "audience", "type": "multiselect", "required": False, "group": "you",
     "options": ["families", "young", "older", "locals", "tourists", "business", "everyone"],
     "default": []},
    {"id": "strengths", "type": "multiselect", "required": False, "group": "you",
     "options": ["price", "quality", "service", "experience", "reliability", "local", "choice"],
     "default": []},
    {"id": "area", "type": "select", "required": True, "group": "you",
     "options": ["local", "region", "country", "online"]},
    {"id": "years", "type": "select", "required": False, "group": "you",
     "options": ["new", "few", "ten", "twentyfive"]},
    # 2) Your website
    {"id": "goal", "type": "multiselect", "required": True, "group": "website",
     "options": ["calls", "bookings", "show", "sell", "visit", "inform"],
     "default": []},
    {"id": "pages", "type": "multiselect", "required": True, "group": "website",
     "options": ["home", "about", "services", "gallery", "pricing", "reviews", "contact"],
     "default": ["home", "about", "services", "contact"]},
    {"id": "features", "type": "multiselect", "required": False, "group": "website",
     "options": ["booking", "contactform", "map", "gallery", "reviews", "shop", "newsletter"],
     "default": []},
    # 3) Overall look
    {"id": "feel", "type": "select", "required": True, "group": "look",
     "options": ["warm", "professional", "modern", "classic"]},
    {"id": "imagery", "type": "select", "required": False, "group": "look",
     "options": ["photos", "text", "graphics", "mix"]},
    {"id": "logo", "type": "select", "required": False, "group": "look",
     "options": ["have", "need", "unsure"]},
    {"id": "example", "type": "text", "required": False, "group": "look"},
    # 4) Dynamic (movement & energy)
    {"id": "motion", "type": "select", "required": False, "group": "dynamic",
     "options": ["still", "gentle", "lively"]},
    {"id": "intensity", "type": "select", "required": False, "group": "dynamic",
     "options": ["calm", "balanced", "bold"]},
    # 5) Colours
    {"id": "colors", "type": "select", "required": True, "group": "color",
     "options": ["blue", "green", "warm", "elegant", "neutral", "designer"],
     "default": "designer"},
    {"id": "theme", "type": "select", "required": False, "group": "color",
     "options": ["light", "dark", "auto"], "default": "auto"},
]

_BY_ID = {q["id"]: q for q in QUESTIONS}


@dataclass
class Brief:
    """Normalized, validated answers (all choices as stable value keys)."""

    name: str
    business_type: str
    area: str
    goal: list[str]             # value keys: "calls", "bookings", …
    pages: list[str]            # value keys: "home", "about", …
    feel: str
    colors: str
    lang: str = "en"
    offerings: str = ""
    audience: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    years: str = ""
    features: list[str] = field(default_factory=list)
    logo: str = ""
    example: str = ""
    imagery: str = ""
    motion: str = ""
    intensity: str = ""
    theme: str = ""

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

        return cls(
            name=answers["name"].strip(),
            business_type=answers.get("business_type", ""),
            area=answers.get("area", ""),
            goal=as_list(answers.get("goal"), []),
            pages=pages,
            feel=answers.get("feel", ""),
            colors=answers.get("colors") or "designer",
            lang=lang,
            offerings=(answers.get("offerings") or "").strip(),
            audience=as_list(answers.get("audience"), []),
            strengths=as_list(answers.get("strengths"), []),
            years=answers.get("years", ""),
            features=as_list(answers.get("features"), []),
            logo=answers.get("logo", ""),
            example=(answers.get("example") or "").strip(),
            imagery=answers.get("imagery", ""),
            motion=answers.get("motion", ""),
            intensity=answers.get("intensity", ""),
            theme=answers.get("theme") or "auto",
        )
