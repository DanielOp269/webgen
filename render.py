"""Turns a Brief + a design direction into a multi-page static site.

A "direction" is a self-contained look (palette, fonts, hero treatment). All
visible copy is pulled from i18n by `brief.lang`, so the generated website comes
out in the customer's language. Each variant is a dict of {filename: html} with
inlined CSS, fully portable (web fonts degrade to system fonts).
"""

from __future__ import annotations

import html
import time
from dataclasses import dataclass

from . import i18n
from .brief import Brief


@dataclass
class Direction:
    key: str            # stable key; title/blurb come from i18n
    accent: str
    accent2: str
    bg: str
    surface: str
    ink: str
    muted: str
    heading_font: str
    body_font: str
    radius: str
    hero: str           # "split" | "gradient" | "centered"


DIRECTIONS: list[Direction] = [
    Direction(
        key="modern", accent="#2563eb", accent2="#60a5fa",
        bg="#ffffff", surface="#f8fafc", ink="#0f172a", muted="#64748b",
        heading_font='-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        body_font='-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        radius="14px", hero="split",
    ),
    Direction(
        key="bold", accent="#7c3aed", accent2="#ec4899",
        bg="#0b0b14", surface="#161626", ink="#f5f5fa", muted="#a5a5c0",
        heading_font='"Segoe UI", system-ui, sans-serif',
        body_font='"Segoe UI", system-ui, sans-serif',
        radius="20px", hero="gradient",
    ),
    Direction(
        key="elegant", accent="#9a7b4f", accent2="#c2a878",
        bg="#fbfaf7", surface="#ffffff", ink="#2b2724", muted="#7c736a",
        heading_font='Georgia, "Times New Roman", serif',
        body_font='Georgia, "Times New Roman", serif',
        radius="6px", hero="centered",
    ),
]

DIRECTIONS_BY_KEY = {d.key: d for d in DIRECTIONS}


def pick_directions(brief: Brief, n: int = 3) -> list[Direction]:
    """Choose up to `n` directions, leading with an explicit style preference."""
    pref = brief.style if brief.style in DIRECTIONS_BY_KEY else None
    if pref:
        ordered = [DIRECTIONS_BY_KEY[pref]] + [d for d in DIRECTIONS if d.key != pref]
    else:                               # "surprise" → one of each
        ordered = list(DIRECTIONS)
    return ordered[:n]


# --------------------------------------------------------------------------
# Copy helpers (the seam a ClaudeGenerator would replace with real copy)
# --------------------------------------------------------------------------

def _services(brief: Brief, S: dict) -> list[str]:
    return brief.services if brief.services else list(S["fallback_services"])


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _filename(page_key: str) -> str:
    return "index.html" if page_key == "home" else page_key + ".html"


def _css(d: Direction) -> str:
    hero_bg = {
        "split": d.bg,
        "gradient": f"linear-gradient(135deg, {d.accent} 0%, {d.accent2} 100%)",
        "centered": d.surface,
    }[d.hero]
    hero_ink = "#ffffff" if d.hero == "gradient" else d.ink
    return f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: {d.body_font}; color: {d.ink}; background: {d.bg};
       line-height: 1.6; -webkit-font-smoothing: antialiased; }}
h1, h2, h3 {{ font-family: {d.heading_font}; line-height: 1.15; color: {d.ink}; }}
a {{ color: {d.accent}; text-decoration: none; }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }}
header.nav {{ position: sticky; top: 0; z-index: 10; background: {d.bg}cc;
             backdrop-filter: blur(8px); border-bottom: 1px solid {d.muted}22; }}
.nav .wrap {{ display: flex; align-items: center; justify-content: space-between;
             height: 68px; }}
.brand {{ font-family: {d.heading_font}; font-weight: 700; font-size: 20px;
         color: {d.ink}; }}
.nav nav {{ display: flex; gap: 22px; flex-wrap: wrap; }}
.nav nav a {{ color: {d.muted}; font-size: 15px; }}
.nav nav a:hover {{ color: {d.accent}; }}
.btn {{ display: inline-block; background: {d.accent}; color: #fff;
       padding: 12px 22px; border-radius: {d.radius}; font-weight: 600;
       border: none; cursor: pointer; }}
.btn:hover {{ filter: brightness(1.07); }}
.hero {{ background: {hero_bg}; color: {hero_ink}; padding: 96px 0; }}
.hero h1 {{ font-size: 52px; color: {hero_ink}; max-width: 16ch; }}
.hero p {{ font-size: 20px; margin: 20px 0 28px; max-width: 52ch;
          color: {hero_ink}; opacity: .9; }}
.hero.split .wrap {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 40px;
                    align-items: center; }}
.hero.split .art {{ height: 280px; border-radius: {d.radius};
   background: linear-gradient(135deg, {d.accent} 0%, {d.accent2} 100%); }}
.hero.centered {{ text-align: center; }}
.hero.centered h1, .hero.centered p {{ margin-left: auto; margin-right: auto; }}
section {{ padding: 72px 0; }}
.eyebrow {{ color: {d.accent}; font-weight: 700; letter-spacing: .08em;
           text-transform: uppercase; font-size: 13px; }}
h2 {{ font-size: 34px; margin: 8px 0 28px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }}
.card {{ background: {d.surface}; border: 1px solid {d.muted}22; padding: 26px;
        border-radius: {d.radius}; }}
.card h3 {{ font-size: 20px; margin-bottom: 8px; }}
.card p {{ color: {d.muted}; }}
.muted {{ color: {d.muted}; }}
.lead {{ font-size: 19px; max-width: 60ch; color: {d.muted}; }}
.band {{ background: {d.surface}; text-align: center; }}
.band h2 {{ margin-bottom: 8px; }}
form.contact {{ display: grid; gap: 14px; max-width: 520px; }}
form.contact input, form.contact textarea {{ width: 100%; padding: 13px 14px;
   border: 1px solid {d.muted}55; border-radius: {d.radius}; font: inherit;
   background: {d.bg}; color: {d.ink}; }}
footer {{ border-top: 1px solid {d.muted}22; padding: 36px 0; color: {d.muted};
         font-size: 14px; }}
@media (max-width: 760px) {{
  .grid {{ grid-template-columns: 1fr; }}
  .hero.split .wrap {{ grid-template-columns: 1fr; }}
  .hero.split .art {{ display: none; }}
  .hero h1 {{ font-size: 38px; }}
}}
"""


def _nav(brief: Brief, d: Direction) -> str:
    links = []
    for key in brief.pages:
        links.append(f'<a href="{_filename(key)}">'
                     f'{_esc(i18n.page_label(key, brief.lang))}</a>')
    return f"""<header class="nav"><div class="wrap">
  <span class="brand">{_esc(brief.name)}</span>
  <nav>{''.join(links)}</nav>
</div></header>"""


def _footer(brief: Brief, S: dict) -> str:
    year = time.localtime().tm_year
    return f"""<footer><div class="wrap">
  © {year} {_esc(brief.name)}. {_esc(S['footer_rights'])}
</div></footer>"""


def _hero(brief: Brief, d: Direction) -> str:
    headline = brief.tagline or brief.name
    cta = f'<a class="btn" href="{_filename("contact")}">{_esc(brief.cta)}</a>'
    art = '<div class="art"></div>' if d.hero == "split" else ""
    inner = f"""<div>
      <h1>{_esc(headline)}</h1>
      <p>{_esc(brief.industry)}</p>
      {cta}
    </div>{art}"""
    return f'<section class="hero {d.hero}"><div class="wrap">{inner}</div></section>'


def _blurb_for(service: str, S: dict) -> str:
    return S["service_blurb"].format(s=service)


def _features(brief: Brief, S: dict) -> str:
    cards = "".join(
        f'<div class="card"><h3>{_esc(s)}</h3><p>{_esc(_blurb_for(s, S))}</p></div>'
        for s in _services(brief, S)[:3]
    )
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['features_eyebrow'])}</span>
  <h2>{_esc(S['features_h2'])}</h2>
  <div class="grid">{cards}</div>
</div></section>"""


def _cta_band(brief: Brief, S: dict) -> str:
    return f"""<section class="band"><div class="wrap">
  <h2>{_esc(S['tone'][brief.tone])}</h2>
  <p class="muted" style="margin-bottom:22px">{_esc(S['band_p'])}</p>
  <a class="btn" href="{_filename('contact')}">{_esc(brief.cta)}</a>
</div></section>"""


# --- per-page bodies (keyed by page value key) -----------------------------

def _page_home(brief, d, S):
    return _hero(brief, d) + _features(brief, S) + _cta_band(brief, S)


def _page_about(brief, d, S):
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['about_eyebrow'])}</span>
  <h2>{_esc(S['about_h2'].format(name=brief.name))}</h2>
  <p class="lead">{_esc(brief.industry)}</p>
  <p class="lead" style="margin-top:18px">{_esc(S['about_p2'])}</p>
</div></section>"""


def _page_services(brief, d, S):
    cards = "".join(
        f'<div class="card"><h3>{_esc(s)}</h3><p>{_esc(_blurb_for(s, S))}</p></div>'
        for s in _services(brief, S)
    )
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['services_eyebrow'])}</span>
  <h2>{_esc(S['services_h2'])}</h2>
  <div class="grid">{cards}</div>
</div></section>""" + _cta_band(brief, S)


def _page_portfolio(brief, d, S):
    tiles = "".join(
        f'<div class="card" style="height:180px;background:linear-gradient(135deg,'
        f'{d.accent},{d.accent2})"></div>'
        for _ in range(6)
    )
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['portfolio_eyebrow'])}</span>
  <h2>{_esc(S['portfolio_h2'])}</h2>
  <div class="grid">{tiles}</div>
</div></section>"""


def _page_pricing(brief, d, S):
    cards = "".join(
        f'<div class="card"><span class="eyebrow">{_esc(t)}</span>'
        f'<h2 style="margin:6px 0">{"$" * (i + 1)}</h2>'
        f'<p class="muted">{_esc(S["pricing_card_p"])}</p>'
        f'<a class="btn" style="margin-top:14px" href="{_filename("contact")}">'
        f'{_esc(brief.cta)}</a></div>'
        for i, t in enumerate(S["pricing_tiers"])
    )
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['pricing_eyebrow'])}</span>
  <h2>{_esc(S['pricing_h2'])}</h2>
  <div class="grid">{cards}</div>
</div></section>"""


def _page_contact(brief, d, S):
    return f"""<section><div class="wrap">
  <span class="eyebrow">{_esc(S['contact_eyebrow'])}</span>
  <h2>{_esc(brief.cta)}</h2>
  <p class="lead" style="margin-bottom:24px">{_esc(S['contact_lead'])}</p>
  <form class="contact" onsubmit="return false">
    <input placeholder="{_esc(S['form_name'])}" />
    <input placeholder="{_esc(S['form_email'])}" type="email" />
    <textarea placeholder="{_esc(S['form_msg'])}" rows="5"></textarea>
    <button class="btn" type="submit">{_esc(brief.cta)}</button>
  </form>
</div></section>"""


_PAGE_BUILDERS = {
    "home": _page_home,
    "about": _page_about,
    "services": _page_services,
    "portfolio": _page_portfolio,
    "pricing": _page_pricing,
    "contact": _page_contact,
}


def render_site(brief: Brief, d: Direction) -> dict[str, str]:
    """Render every requested page for one design direction, in brief.lang."""
    S = i18n.site(brief.lang)
    css = _css(d)
    files: dict[str, str] = {}
    for key in brief.pages:
        builder = _PAGE_BUILDERS.get(key)
        if not builder:
            continue
        body = builder(brief, d, S)
        doc = f"""<!doctype html>
<html lang="{_esc(brief.lang)}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(brief.name)} — {_esc(i18n.page_label(key, brief.lang))}</title>
<style>{css}</style>
</head><body>
{_nav(brief, d)}
{body}
{_footer(brief, S)}
</body></html>"""
        files[_filename(key)] = doc
    return files
