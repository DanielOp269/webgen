"""Pluggable site editors — apply a customer's plain-language change to a site.

Mirrors generator.py: the rest of the pipeline only knows the `Editor` interface,
so the real (browser) editor and the offline stub are interchangeable.

  BrowserEditor — reopens the variant's claude.ai conversation and sends the
                  change as one follow-up turn, then scrapes the revised HTML.
                  This is the whole point of persisting each variant's chat_url.
  StubEditor    — deterministic, offline: annotates the pages so the round-trip
                  (request → worker applies → live site updates) is observable
                  and testable without a browser.

The worker applies edits asynchronously (the browser is slow + serialized), the
same way it runs generation.
"""

from __future__ import annotations

import html
import os
import re

from .agent import Variant
from .brief import Brief

_IMG_URL = re.compile(r"/c/[A-Za-z0-9_-]+/img/[A-Za-z0-9._-]+")


class Editor:
    """Applies `instruction` to `variant`, returning the revised {filename: html}."""

    name = "base"

    def edit(self, brief: Brief, variant: Variant, instruction: str) -> dict[str, str]:
        raise NotImplementedError


class BrowserEditor(Editor):
    """Real edits via claude.ai: reopen the conversation, send one more turn."""

    name = "browser"

    def edit(self, brief: Brief, variant: Variant, instruction: str) -> dict[str, str]:
        from . import browser

        if not variant.chat_url:
            raise RuntimeError("no chat_url on this variant — can't reopen the "
                               "conversation to edit it")
        headless = os.environ.get("WEBGEN_HEADLESS", "").lower() in ("1", "true", "yes")
        revised = browser.send_edit(variant.chat_url, instruction, headless=headless)
        if not revised:
            raise RuntimeError("browser edit produced no HTML")
        return {"index.html": revised}


class StubEditor(Editor):
    """Offline stand-in for the real (browser) editor.

    Not an AI edit — it can't rewrite copy or restyle — so it only does the one
    thing it can do cleanly and visibly: when photos are attached, add a tidy
    gallery of them. It never renders debug text or the raw instruction onto the
    page (that internal prompt is only meaningful to the real editor).
    """

    name = "stub"

    def edit(self, brief: Brief, variant: Variant, instruction: str) -> dict[str, str]:
        imgs = _IMG_URL.findall(instruction)
        if not imgs:
            return dict(variant.files)          # nothing this stub can do — leave as-is
        tiles = "".join(
            f'<img src="{html.escape(u)}" alt="" loading="lazy" '
            f'style="width:100%;height:240px;object-fit:cover;border-radius:12px">'
            for u in imgs
        )
        heading = "Galerie" if brief.lang == "de" else "Gallery"
        gallery = (
            '<section style="padding:72px 24px">'
            '<div style="max-width:1080px;margin:0 auto">'
            f'<h2 style="text-align:center;font-size:32px;margin:0 0 28px">{heading}</h2>'
            '<div style="display:grid;gap:18px;'
            'grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">'
            f'{tiles}</div></div></section>'
        )
        revised = dict(variant.files)
        home = "index.html"
        if home in revised and "</body>" in revised[home].lower():
            doc = revised[home]
            idx = doc.lower().rfind("</body>")
            revised[home] = doc[:idx] + gallery + doc[idx:]
        return revised


def default_editor() -> Editor:
    """Pick the editor to match the generation engine (WEBGEN_ENGINE)."""
    if os.environ.get("WEBGEN_ENGINE", "").lower() == "browser":
        return BrowserEditor()
    return StubEditor()
