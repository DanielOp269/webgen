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
    """Offline stand-in: apply a visible, deterministic change to each page.

    Not a real edit — it just proves the plumbing end to end without a browser.
    """

    name = "stub"

    def edit(self, brief: Brief, variant: Variant, instruction: str) -> dict[str, str]:
        note = f"<!-- edit applied: {instruction} -->"
        banner = (f'<div style="background:#16a34a;color:#fff;padding:10px 16px;'
                  f'font:14px/1.4 sans-serif;text-align:center">'
                  f'✎ {html.escape(instruction)}</div>')
        # Attached photos → drop them onto the (home) page so the loop is visible.
        imgs = _IMG_URL.findall(instruction)
        gallery = ""
        if imgs:
            tiles = "".join(
                f'<img src="{html.escape(u)}" alt="" '
                f'style="width:220px;height:160px;object-fit:cover;border-radius:8px">'
                for u in imgs
            )
            gallery = (f'<div style="display:flex;gap:12px;flex-wrap:wrap;'
                       f'justify-content:center;padding:24px">{tiles}</div>')
        revised: dict[str, str] = {}
        for fname, doc in variant.files.items():
            add = banner + (gallery if fname == "index.html" else "")
            if "<body>" in doc:
                doc = doc.replace("<body>", "<body>\n" + add, 1)
            revised[fname] = note + "\n" + doc
        return revised


def default_editor() -> Editor:
    """Pick the editor to match the generation engine (WEBGEN_ENGINE)."""
    if os.environ.get("WEBGEN_ENGINE", "").lower() == "browser":
        return BrowserEditor()
    return StubEditor()
