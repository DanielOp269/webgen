"""Pluggable site generators.

The agent only knows the `Generator` interface, so swapping the template engine
for real AI generation is a one-class change with no edits elsewhere.

  TemplateGenerator  — deterministic, offline, $0 (the default, works today).
  ClaudeGenerator    — calls the Claude API via stdlib urllib (no SDK/pip).
                       Stubbed until an API key is available; the wiring it
                       needs is sketched in the docstring.
"""

from __future__ import annotations

import os

from .brief import Brief
from .render import Direction, render_site

# The reworked brief's `feel` choice → a natural-language tone for the prompt.
_FEEL_TONE = {
    "warm": "warm and welcoming",
    "professional": "professional and trustworthy",
    "modern": "modern and confident",
    "classic": "refined and elegant",
}


def _describe_brief(brief: Brief, i18n) -> str:
    """Compose a natural-language business summary from the brief's answers.

    The reworked brief captures the business as structured choices (+ optional
    free text) rather than one `industry` blurb, so we stitch the meaningful
    parts into a paragraph the generation prompt can work from.
    """
    lang = brief.lang
    label = lambda qid, key: i18n.option_label(qid, key, lang)
    parts = []
    btype = label("business_type", brief.business_type)
    parts.append(f"{btype}: {brief.offerings.rstrip('.')}" if brief.offerings else btype)
    if brief.audience:
        parts.append("Serving " + ", ".join(label("audience", a) for a in brief.audience))
    if brief.strengths:
        parts.append("Known for " + ", ".join(label("strengths", s) for s in brief.strengths))
    if brief.goal:
        parts.append("The site should " + ", ".join(label("goal", g) for g in brief.goal))
    return ". ".join(parts)


class Generator:
    """Produces {filename: html} for one Brief + Direction."""

    name = "base"
    variants = 3            # default number of design options a job produces

    def generate(self, brief: Brief, direction: Direction) -> dict[str, str]:
        raise NotImplementedError


class TemplateGenerator(Generator):
    """Fills the multi-page templates from the brief. Fully offline."""

    name = "template"

    def generate(self, brief: Brief, direction: Direction) -> dict[str, str]:
        return render_site(brief, direction)


class ClaudeGenerator(Generator):
    """Generate sites with the Claude API using only the standard library.

    Drop-in upgrade path (no extra deps): read ANTHROPIC_API_KEY from the env,
    POST to https://api.anthropic.com/v1/messages with urllib.request, and ask
    Claude (model "claude-opus-4-8") to return the HTML for each page given the
    brief and the chosen Direction's palette/fonts. Parse the JSON, map page ->
    html, and return the same {filename: html} shape TemplateGenerator returns —
    so the agent and server need zero changes.

    Left intentionally unimplemented until a key is provided; falls back to the
    template engine so the app keeps working in the meantime.
    """

    name = "claude"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._fallback = TemplateGenerator()

    def generate(self, brief: Brief, direction: Direction) -> dict[str, str]:
        if not self.api_key:
            return self._fallback.generate(brief, direction)
        raise NotImplementedError(
            "Claude generation not wired yet — see ClaudeGenerator docstring."
        )


class BrowserGenerator(Generator):
    """Generate a real site by driving claude.ai in a browser (see browser.py).

    Each Direction maps to a distinct prompt aesthetic, so variants look
    genuinely different. Slow (minutes) and serialized (one browser at a time),
    so it defaults to a single variant per job.
    """

    name = "browser"
    variants = 1

    def __init__(self):
        self.chat_url = ""              # conversation for the last generate() (read by the Job)

    def generate(self, brief: Brief, direction: Direction) -> dict[str, str]:
        from . import browser, i18n

        self.chat_url = ""
        prompt = browser.site_prompt(
            brief.name, _describe_brief(brief, i18n),
            tone=_FEEL_TONE.get(brief.feel, "warm and confident"),
            language=i18n.LANG_NAMES.get(brief.lang, "English"),
            aesthetic=direction.key,
        )
        headless = os.environ.get("WEBGEN_HEADLESS", "").lower() in ("1", "true", "yes")
        html, chat_url = browser.generate_html(prompt, refine=browser.REFINE_PROMPT,
                                               headless=headless)
        if not html:
            raise RuntimeError("browser generation produced no HTML")
        self.chat_url = chat_url or ""
        return {"index.html": html}


def default_generator() -> Generator:
    """Pick the engine. WEBGEN_ENGINE overrides; else Claude-API-when-keyed, else template."""
    engine = os.environ.get("WEBGEN_ENGINE", "").lower()
    if engine == "browser":
        return BrowserGenerator()
    if engine in ("template", "offline"):
        return TemplateGenerator()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return ClaudeGenerator(key)
    return TemplateGenerator()
