"""Browser automation plumbing for the claude.ai generation engine.

The whole approach hinges on a *persistent* logged-in Chromium profile: you log
into claude.ai once (manually), the cookies/session are saved to disk, and every
later generation run reuses that same profile so it's already authenticated.

This module owns that profile and how the browser is launched. Run it directly
to do the one-time login:

    .venv/bin/python browser.py login        # opens a window; log in, then press Enter
    .venv/bin/python browser.py check         # reports whether the saved session is still valid
    .venv/bin/python browser.py gen           # run a sample generation, save out.html
"""

from __future__ import annotations

import os
import sys
import threading

# Only one persistent-profile browser can run at a time (the profile is locked
# on disk). Serialize all browser use so concurrent jobs queue instead of
# crashing with "profile already in use".
_BROWSER_LOCK = threading.Lock()

# Logged-in profile lives next to this file (gitignored — it holds your session).
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_profile")

CLAUDE_URL = "https://claude.ai"

# A normal-looking desktop Chrome UA / viewport — less likely to trip bot checks
# than Playwright's headless defaults.
VIEWPORT = {"width": 1440, "height": 900}


def launch(playwright, *, headless: bool = False):
    """Open the persistent Chromium context (already logged in, once set up).

    Returns a BrowserContext. Headful by default; pass headless=True only where a
    real/virtual display isn't available. On a Linux server prefer headful under
    Xvfb instead of true headless — claude.ai's bot checks tolerate it better.
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        viewport=VIEWPORT,
        args=["--disable-blink-features=AutomationControlled"],
    )


def _logged_in(page) -> bool:
    """Heuristic: on claude.ai, a logged-out session lands on /login."""
    return "/login" not in page.url


def login() -> None:
    """One-time manual login. Opens a window; you sign in, then press Enter."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = launch(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CLAUDE_URL, wait_until="domcontentloaded")
        print("\nA browser window opened. Log into claude.ai there.")
        print("When you can see your chat list, come back here and press Enter…")
        input()
        page.goto(CLAUDE_URL, wait_until="domcontentloaded")
        ok = _logged_in(page)
        print("✅ Session saved — you're logged in." if ok
              else "⚠️  Still on the login page; session not saved. Try again.")
        ctx.close()


def check() -> None:
    """Headless check that the saved session is still valid (no UI)."""
    from playwright.sync_api import sync_playwright

    if not os.path.isdir(PROFILE_DIR):
        print("❌ No profile yet — run:  python browser.py login")
        return
    with sync_playwright() as p:
        ctx = launch(p, headless=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CLAUDE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        print("✅ Logged in." if _logged_in(page)
              else "❌ Logged out — run:  python browser.py login")
        ctx.close()


NEW_CHAT_URL = "https://claude.ai/new"
_DIAG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag")

# A single self-contained HTML page, returned as one fenced code block so it's
# trivial to scrape. We explicitly ask Claude NOT to use Artifacts.
PROMPT_TEMPLATE = """\
Build a complete, modern, production-quality single-page marketing website for \
this business, as ONE self-contained HTML file: inline all CSS in a <style> tag \
and any JS in a <script> tag, make it fully responsive, and use a polished, \
contemporary design with real section copy (hero, what they do, why choose them, \
and a contact section).

Business name: {name}
What they do: {industry}
Tone: {tone}

Important output rules:
- Do NOT use the Artifacts feature.
- Reply with ONLY the HTML, inside a single ```html code block.
- No explanation or text before or after the code block.
"""

SAMPLE_PROMPT = PROMPT_TEMPLATE.format(
    name="Marbel & Co.",
    industry="A boutique interior design studio for modern homes and small offices.",
    tone="warm and professional",
)

# --- the "anti-template" prompt, parameterized by a design direction ------
# Each Direction maps to a strong, opinionated aesthetic so different variants
# look genuinely different (not the same template recoloured). Extend this dict
# to grow the design library later.
AESTHETICS = {
    "elegant": (
        "Editorial, warm-minimal luxury. Oversized display serif headlines "
        "(Fraunces / Playfair Display / Cormorant) with a clean grotesque sans "
        "body. Asymmetric magazine grid, generous negative space, an earthy "
        "palette (warm neutrals + one deep accent), hairline rules and "
        "small-caps labels."
    ),
    "modern": (
        "Swiss / International minimalism. A strict visible grid, crisp grotesque "
        "type, a restrained near-monochrome palette with one sharp accent, lots "
        "of whitespace, precise alignment, and subtle micro-interactions. "
        "Tailored and confident, never decorative."
    ),
    "bold": (
        "Expressive and high-impact. Massive type, confident colour blocking in "
        "rich saturated tones (never purple/blue tech gradients), oversized "
        "imagery, strong asymmetry and visual rhythm. Memorable and editorial, "
        "not corporate."
    ),
}
DEFAULT_AESTHETIC = "elegant"

SITE_PROMPT = """\
You are an award-winning web designer (think Awwwards / Godly site of the day). \
Design a genuinely distinctive single-page marketing website — bespoke, NOT a \
generic AI template.

Business name: {name}
What they do: {industry}
Tone of voice: {tone}
Write ALL visible site copy in: {language}

Design direction — commit to it fully:
{direction}

Also: tasteful real imagery (Unsplash source URLs) and/or elegant CSS art; \
restrained motion (gentle fade/parallax on scroll); real, specific, human \
editorial copy — no filler buzzwords.

DO NOT produce the cliché AI look. Avoid: a centered hero with a big gradient, \
three equal feature cards in a row, emoji as icons, the Inter / system-ui font, \
and copy like "Elevate / Empower / Unlock / Transform your X."

Technical: one self-contained HTML file (inline <style>, web fonts via <link>, \
inline <script>), fully responsive and accessible.

Output rules:
- Do NOT use the Artifacts feature.
- Reply with ONLY the HTML in a single ```html code block. No prose.
"""

# A single self-critique/refinement turn, sent after the first reply.
REFINE_PROMPT = """\
Now act as a tough design critic reviewing your own work. Push it further so it \
clearly does NOT look like an AI template:
- Make the typography more dramatic (bigger contrast, a real type scale).
- Add one memorable signature element (an unusual section layout, an editorial \
detail, a distinctive nav or footer).
- Tighten the copy so it sounds written by a human, specific to this business.
- Make sure nothing looks like the default centered-hero + 3-cards pattern.

Return the COMPLETE revised single HTML file again as ONLY a ```html code block, \
no prose, no Artifacts.
"""

# One customer-requested edit, sent as a follow-up turn in the SAME conversation
# (so Claude keeps the full design context and only changes what's asked).
EDIT_PROMPT = """\
The client would like this change to the website:

{instruction}

Apply exactly that change and keep everything else the same. Return the COMPLETE \
updated single HTML file as ONLY a ```html code block — no prose, no Artifacts.
"""


def site_prompt(name: str, industry: str, *, tone: str = "warm and confident",
                language: str = "English", aesthetic: str = DEFAULT_AESTHETIC) -> str:
    """Build the generation prompt for one business + design direction."""
    return SITE_PROMPT.format(
        name=name, industry=industry, tone=tone, language=language,
        direction=AESTHETICS.get(aesthetic, AESTHETICS[DEFAULT_AESTHETIC]),
    )


ANTI_TEMPLATE_SAMPLE = site_prompt(
    "Marbel & Co.",
    "A boutique interior design studio for modern homes and small offices.",
    tone="warm and confident",
)


def _save_diagnostics(page, label: str) -> None:
    os.makedirs(_DIAG_DIR, exist_ok=True)
    try:
        page.screenshot(path=os.path.join(_DIAG_DIR, f"{label}.png"), full_page=True)
    except Exception:
        pass
    try:
        with open(os.path.join(_DIAG_DIR, f"{label}.html"), "w", encoding="utf-8") as fh:
            fh.write(page.content())
    except Exception:
        pass
    print(f"   (diagnostics saved to _diag/{label}.png and _diag/{label}.html)")


def _extract_html(page) -> str | None:
    """Best-effort: pull the generated HTML out of the last assistant reply.

    Tries the markdown code block first (what the prompt asks for); falls back to
    any <pre><code> on the page. Artifact extraction is a later refinement.
    """
    blocks = page.locator("pre code")
    n = blocks.count()
    if not n:
        return None
    # Take the LAST substantial HTML block — after a refinement turn that's the
    # revised page, not the first draft. Fall back to the longest block.
    best, best_len = None, 0
    for i in range(n):
        txt = blocks.nth(i).inner_text()
        if "<" not in txt:
            continue
        if len(txt) > 500:
            best = txt                  # keep overwriting → ends on the last big one
        elif len(txt) > best_len:
            best, best_len = txt, len(txt)
    return best


def _send_and_wait(page, message: str, *, timeout_ms: int = 240_000) -> None:
    """Type a message into the composer, send it, and wait for the reply to finish."""
    editor = page.locator('div[contenteditable="true"]').first
    editor.wait_for(state="visible", timeout=30_000)
    editor.click()
    page.keyboard.insert_text(message)
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    print("→ message sent; waiting for Claude to finish…")

    # Generation is running while a "Stop" button is present.
    stop = page.locator('button[aria-label*="Stop"], button[aria-label*="stop"]')
    try:
        stop.first.wait_for(state="visible", timeout=30_000)
    except Exception:
        print("   (no stop button seen — selector may be off; continuing)")
    try:
        stop.first.wait_for(state="hidden", timeout=timeout_ms)
    except Exception:
        print("   (timed out waiting for completion; trying to extract anyway)")
    page.wait_for_timeout(1500)


def generate_html(prompt: str, *, refine: str | None = None,
                  headless: bool = False, timeout_ms: int = 240_000):
    """Drive claude.ai: send `prompt` (then optional `refine` turn).

    Returns (html, chat_url): the extracted HTML and the conversation's URL, so
    later edits can reopen the same chat. Returns (None, "") on failure.
    """
    from playwright.sync_api import sync_playwright

    with _BROWSER_LOCK, sync_playwright() as p:
        ctx = launch(p, headless=headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(NEW_CHAT_URL, wait_until="domcontentloaded")
            if "/login" in page.url:
                print("❌ Not logged in — run:  python browser.py login")
                return None, ""

            _send_and_wait(page, prompt, timeout_ms=timeout_ms)
            # After the first turn claude.ai navigates to /chat/<id> — capture it.
            chat_url = page.url
            if refine:
                print("→ sending refinement pass…")
                _send_and_wait(page, refine, timeout_ms=timeout_ms)

            html = _extract_html(page)
            if not html:
                print("⚠️  Couldn't find the HTML in the reply.")
                _save_diagnostics(page, "gen-fail")
                return None, chat_url
            print(f"✅ extracted {len(html):,} chars of HTML  (chat: {chat_url})")
            return html, chat_url
        finally:
            ctx.close()


def send_edit(chat_url: str, instruction: str, *, headless: bool = False,
              timeout_ms: int = 240_000):
    """Reopen an existing claude.ai conversation and apply one edit turn.

    Sends `instruction` as a follow-up in the same chat and scrapes the revised
    HTML from the reply. Returns the HTML, or None on failure.
    """
    from playwright.sync_api import sync_playwright

    if not chat_url:
        print("❌ no chat_url — nothing to reopen")
        return None

    with _BROWSER_LOCK, sync_playwright() as p:
        ctx = launch(p, headless=headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(chat_url, wait_until="domcontentloaded")
            if "/login" in page.url:
                print("❌ Not logged in — run:  python browser.py login")
                return None

            _send_and_wait(page, EDIT_PROMPT.format(instruction=instruction),
                           timeout_ms=timeout_ms)
            html = _extract_html(page)
            if not html:
                print("⚠️  Couldn't find the revised HTML in the reply.")
                _save_diagnostics(page, "edit-fail")
                return None
            print(f"✅ edited → {len(html):,} chars of HTML")
            return html
        finally:
            ctx.close()


def gen() -> None:
    """Run one sample generation and save it to out.html (for hands-on testing)."""
    html, _ = generate_html(SAMPLE_PROMPT, headless=False)
    if html:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.html")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"→ wrote {out} — open it in a browser to eyeball the result.")


def gen2() -> None:
    """Anti-template experiment: strongly-directed prompt + a refinement pass."""
    html, _ = generate_html(ANTI_TEMPLATE_SAMPLE, refine=REFINE_PROMPT, headless=False)
    if html:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out2.html")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"→ wrote {out} — compare it against out.html.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "login"
    {"login": login, "check": check, "gen": gen, "gen2": gen2}.get(cmd, login)()
