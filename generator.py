"""Pluggable site generators.

The agent only knows the `Generator` interface, so swapping the template engine
for real AI generation is a one-class change with no edits elsewhere.

  TemplateGenerator  — deterministic, offline, $0 (the default, works today).
  ClaudeGenerator    — calls the Claude API via stdlib urllib (no SDK/pip).
                       Stubbed until an API key is available; the wiring it
                       needs is sketched in the docstring.
"""

from __future__ import annotations

from .brief import Brief
from .render import Direction, render_site


class Generator:
    """Produces {filename: html} for one Brief + Direction."""

    name = "base"

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


def default_generator() -> Generator:
    """Pick the best available engine. Template today; auto-upgrades later."""
    import os

    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return ClaudeGenerator(key)
    return TemplateGenerator()
