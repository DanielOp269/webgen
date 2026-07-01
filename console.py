"""The customer console: the page a lead opens to see their finished options.

Reached at ``/c/<lead_id>`` (later an emailed magic link). It has three states,
driven by the lead's generation job:

  pending  — no job yet, or still running: a reassuring "we're on it" page that
             auto-refreshes so results appear without the customer doing anything.
  ready    — job done: each design option as a card with a live preview iframe,
             an "open full" link, and a download button.
  error    — job failed: a calm "we'll be in touch" message.

Self-contained HTML with inlined CSS, all copy from i18n by the brief's language
(so the console speaks the customer's language). No framework, no build step —
same spirit as render.py.
"""

from __future__ import annotations

import html

from . import i18n
from .agent import Job
from .leads import Lead

_REFRESH_SECONDS = 8


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _css() -> str:
    return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       color: #0f172a; background: #f1f5f9; line-height: 1.6;
       -webkit-font-smoothing: antialiased; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
header.top { background: #ffffff; border-bottom: 1px solid #e2e8f0; padding: 22px 0; }
header.top .brand { font-weight: 700; font-size: 18px; color: #0f172a; }
header.top .for { color: #64748b; font-size: 14px; margin-top: 2px; }
.hero { padding: 48px 0 8px; }
.hero h1 { font-size: 30px; line-height: 1.2; }
.hero p { color: #475569; font-size: 17px; max-width: 60ch; margin-top: 10px; }
main { padding: 24px 0 64px; }
.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;
        margin-top: 24px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
        overflow: hidden; display: flex; flex-direction: column; }
.card.is-chosen { border-color: #16a34a; box-shadow: 0 0 0 3px #16a34a22; }
.badge { display: inline-block; font-size: 12px; font-weight: 700; color: #16a34a;
         background: #16a34a14; border-radius: 999px; padding: 2px 10px;
         vertical-align: middle; }
.card .frame { position: relative; height: 300px; background: #f8fafc;
               border-bottom: 1px solid #e2e8f0; overflow: hidden; }
.card .frame iframe { position: absolute; top: 0; left: 0;
   width: 1280px; height: 960px; border: 0;
   transform: scale(.5625); transform-origin: top left; }
.card .frame a.cover { position: absolute; inset: 0; z-index: 2; }
.card .body { padding: 20px; display: flex; flex-direction: column; gap: 6px;
              flex: 1; }
.card .body h3 { font-size: 19px; }
.card .body p { color: #64748b; font-size: 14px; flex: 1; }
.card .actions { display: flex; gap: 10px; align-items: center;
                 margin-top: 12px; }
.dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.btn { display: inline-block; border-radius: 10px; padding: 10px 16px;
       font-weight: 600; font-size: 14px; cursor: pointer; text-decoration: none; }
.btn.primary { background: #2563eb; color: #fff; border: 0; font: inherit;
               font-weight: 600; }
.btn.primary:hover { filter: brightness(1.07); }
.btn.primary.chosen { background: #16a34a; cursor: default; }
.btn.ghost { color: #2563eb; }
.actions form { margin: 0; }
.hero.confirmed { padding-top: 40px; }
.hero.confirmed .check { width: 46px; height: 46px; border-radius: 50%;
   background: #16a34a; color: #fff; font-size: 26px; font-weight: 700;
   display: flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.hero.confirmed h1 { color: #15803d; }
.hero.confirmed .cta-row { display: flex; gap: 12px; align-items: center;
   flex-wrap: wrap; margin-top: 18px; }
.hero.confirmed .btn.edit { background: #16a34a; padding: 13px 24px; font-size: 16px; }
.hero.confirmed .btn.edit:hover { filter: brightness(1.05); }
.editbox { margin-top: 26px; max-width: 560px; background: #fff;
   border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; text-align: left; }
.editbox label { display: block; font-weight: 600; font-size: 15px;
   color: #0f172a; margin-bottom: 8px; }
.editbox textarea { width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1;
   border-radius: 10px; font: inherit; resize: vertical; color: #0f172a; }
.editbox textarea:focus { outline: none; border-color: #2563eb; }
.editbox .btn { margin-top: 10px; }
.state { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
         padding: 48px 40px; text-align: center; margin-top: 32px; }
.state h1 { font-size: 26px; margin-bottom: 10px; }
.state p { color: #475569; max-width: 52ch; margin: 0 auto; }
.spinner { width: 34px; height: 34px; margin: 0 auto 20px;
   border: 3px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%;
   animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
footer { color: #94a3b8; font-size: 13px; text-align: center; padding: 28px 0; }
@media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
"""


def _shell(lang: str, brand: str, sub: str, body: str, *, refresh: bool) -> str:
    U = i18n.ui(lang)
    meta_refresh = (f'<meta http-equiv="refresh" content="{_REFRESH_SECONDS}">'
                    if refresh else "")
    top = ""
    if brand:
        top = (f'<header class="top"><div class="wrap">'
               f'<div class="brand">{_esc(brand)}</div>'
               f'<div class="for">{_esc(sub)}</div></div></header>')
    return f"""<!doctype html>
<html lang="{_esc(lang)}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
{meta_refresh}
<title>{_esc(U['console_title'])}</title>
<style>{_css()}</style>
</head><body>
{top}
{body}
<footer>{_esc(U['app_footer'])}</footer>
</body></html>"""


def _state_page(lang: str, brand: str, sub: str, heading: str, message: str,
                *, spinner: bool, refresh: bool) -> str:
    spin = '<div class="spinner"></div>' if spinner else ""
    body = (f'<main><div class="wrap"><div class="state">{spin}'
            f'<h1>{_esc(heading)}</h1><p>{_esc(message)}</p>'
            f'</div></div></main>')
    return _shell(lang, brand, sub, body, refresh=refresh)


def _variant_card(lead: Lead, v_key: str, title: str, blurb: str, accent: str,
                  chosen: bool, U: dict) -> str:
    base = f"/c/{_esc(lead.id)}/v/{_esc(v_key)}"
    badge = (f'<span class="badge">{_esc(U["console_chosen_badge"])}</span>'
             if chosen else "")
    # The primary action is choosing. A chosen card shows a settled "Selected"
    # state instead of the button; other cards let the customer switch to them.
    if chosen:
        choose = f'<span class="btn primary chosen">{_esc(U["console_selected"])}</span>'
    else:
        choose = (f'<form method="post" action="/c/{_esc(lead.id)}/choose">'
                  f'<input type="hidden" name="variant" value="{_esc(v_key)}">'
                  f'<button class="btn primary" type="submit">'
                  f'{_esc(U["console_choose"])}</button></form>')
    return f"""<div class="card{' is-chosen' if chosen else ''}">
  <div class="frame">
    <iframe src="{base}/site/index.html" loading="lazy" scrolling="no"
            title="{_esc(title)}"></iframe>
    <a class="cover" href="{base}/site/index.html" target="_blank"
       rel="noopener" aria-label="{_esc(U['console_open'])}"></a>
  </div>
  <div class="body">
    <h3><span class="dot" style="background:{_esc(accent)}"></span> {_esc(title)} {badge}</h3>
    <p>{_esc(blurb)}</p>
    <div class="actions">
      {choose}
      <a class="btn ghost" href="{base}/site/index.html" target="_blank"
         rel="noopener">{_esc(U['console_open'])}</a>
    </div>
  </div>
</div>"""


def render_page(lead: Lead | None, job: Job | None, lang: str) -> str:
    """Full console HTML for a lead's current generation state."""
    U = i18n.ui(lang)

    if lead is None:
        return _state_page(lang, "", "", U["console_notfound_h"],
                           U["console_notfound_sub"], spinner=False, refresh=False)

    brand = lead.brief.name
    sub = U["console_for"].format(name=lead.contact.name or brand)

    # No job yet, or still queued/running → keep the customer reassured + poll.
    if job is None or job.status in ("queued", "running"):
        return _state_page(lang, brand, sub, U["console_pending_h"],
                           U["console_pending_sub"], spinner=True, refresh=True)

    if job.status == "error" or not job.variants:
        return _state_page(lang, brand, sub, U["console_error_h"],
                           U["console_error_sub"], spinner=False, refresh=False)

    # A customer-requested change is being applied → reassure + poll for the result.
    if job.edit_status in ("pending", "applying"):
        return _state_page(lang, brand, sub, U["console_editing_h"],
                           U["console_editing_sub"], spinner=True, refresh=True)

    chosen = job.chosen
    cards = "".join(
        _variant_card(lead, v.key, v.title, v.blurb, v.accent,
                      chosen == v.key, U)
        for v in job.variants
    )

    if chosen and job.variant(chosen):
        # Confirmation banner leads; the grid stays below so they can switch.
        title = job.variant(chosen).title
        heading = U["console_chosen_h"]
        sub_msg = U["console_chosen_sub"].format(title=title)
        edit_box = f"""<form class="editbox" method="post"
        action="/c/{_esc(lead.id)}/edit">
    <label>{_esc(U['console_edit_label'])}</label>
    <textarea name="instruction" rows="2" required
              placeholder="{_esc(U['console_edit_ph'])}"></textarea>
    <button class="btn primary" type="submit">{_esc(U['console_edit_btn'])}</button>
  </form>"""
        hero = f"""<section class="hero confirmed"><div class="wrap">
  <div class="check">✓</div>
  <h1>{_esc(heading)}</h1>
  <p>{_esc(sub_msg)}</p>
  <div class="cta-row">
    <a class="btn primary edit" href="/c/{_esc(lead.id)}/editor">{_esc(U['console_edit_open'])}</a>
    <a class="btn ghost" href="/site/{_esc(lead.id)}/" target="_blank"
       rel="noopener">{_esc(U['console_visit'])}</a>
  </div>
  {edit_box}
</div></section>"""
    else:
        hero = f"""<section class="hero"><div class="wrap">
  <h1>{_esc(U['console_ready_h'])}</h1>
  <p>{_esc(U['console_ready_sub'])}</p>
</div></section>"""

    body = f"""{hero}
<main><div class="wrap"><div class="grid">{cards}</div></div></main>"""
    return _shell(lang, brand, sub, body, refresh=False)
