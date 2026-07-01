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
.btn.big { display: block; width: 100%; text-align: center; padding: 15px 18px;
   font-size: 16px; margin-bottom: 12px; }
.btn.edit { background: #16a34a; color: #fff; border: 0; font: inherit; font-weight: 600; }
.btn.edit:hover { filter: brightness(1.06); }
.btn.outline { background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; }
.btn.outline:hover { border-color: #94a3b8; }
.actions form { margin: 0; }

/* chosen → "My Website" dashboard */
.dash { padding: 40px 0 16px; }
.live-note { display: flex; align-items: center; gap: 9px; color: #15803d;
   font-weight: 700; font-size: 16px; margin-bottom: 16px; }
.live-note .check { width: 26px; height: 26px; border-radius: 50%; background: #16a34a;
   color: #fff; font-size: 15px; display: inline-flex; align-items: center;
   justify-content: center; }
.mywebsite { display: grid; grid-template-columns: 1.35fr 1fr; gap: 28px;
   align-items: center; background: #fff; border: 1px solid #e2e8f0;
   border-radius: 18px; padding: 22px; }
.mywebsite .preview { position: relative; height: 340px; overflow: hidden;
   border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
.mywebsite .preview iframe { position: absolute; top: 0; left: 0; width: 1280px;
   height: 1000px; border: 0; transform: scale(.53); transform-origin: top left; }
.mywebsite .preview .cover { position: absolute; inset: 0; }
.mywebsite .panel h1 { font-size: 26px; }
.mywebsite .panel .design { display: flex; align-items: center; gap: 8px;
   color: #64748b; font-size: 14px; margin: 8px 0 22px; }
.mywebsite .panel .hint { color: #94a3b8; font-size: 13px; margin-top: 4px; }
.others { padding: 24px 0 60px; }
.others-h { font-size: 18px; color: #334155; margin-bottom: 16px; }
@media (max-width: 760px) { .mywebsite { grid-template-columns: 1fr; } }

/* ---- console shell (left-nav dashboard) ---- */
body.app { background: #f7f8fa; color: #111827; }
.console { display: grid; grid-template-columns: 264px 1fr; min-height: 100vh; }
.side { background: #fff; border-right: 1px solid #edeff2; padding: 16px 12px;
   display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; }
.brand { display: flex; align-items: center; gap: 11px; padding: 8px 8px 16px; }
.brand .logo { width: 38px; height: 38px; border-radius: 9px; flex: none;
   background: linear-gradient(135deg, #16a34a, #157f43); color: #fff;
   font-weight: 800; font-size: 14px; letter-spacing: .02em;
   display: flex; align-items: center; justify-content: center; }
.brand .bn { font-weight: 700; font-size: 14px; line-height: 1.25; color: #111827; }
.brand .bt { font-size: 12px; color: #9aa3af; margin-top: 2px; }
.side nav { display: flex; flex-direction: column; gap: 2px; }
.nav-item { display: flex; align-items: center; gap: 11px; padding: 9px 11px;
   border-radius: 8px; color: #4b5563; font-weight: 500; font-size: 14.5px;
   text-decoration: none; }
.nav-item svg { width: 19px; height: 19px; color: #9aa3af; flex: none; }
.nav-item:hover { background: #f4f5f7; color: #111827; }
.nav-item:hover svg { color: #6b7280; }
.nav-item.active { background: #f0fdf4; color: #15803d; font-weight: 600; }
.nav-item.active svg { color: #16a34a; }
.side .spacer { flex: 1; }
.side .foot { border-top: 1px solid #edeff2; padding: 12px 8px 2px;
   color: #9aa3af; font-size: 11.5px; }
.content { min-width: 0; }
.chead { background: #fff; border-bottom: 1px solid #edeff2; padding: 0 32px;
   height: 64px; display: flex; align-items: center; justify-content: space-between;
   position: sticky; top: 0; z-index: 5; }
.chead h1 { font-size: 18px; font-weight: 600; letter-spacing: -.01em; }
.live-dot { display: inline-flex; align-items: center; gap: 7px; background: #f0fdf4;
   color: #15803d; font-weight: 600; font-size: 12.5px; padding: 5px 11px;
   border-radius: 999px; }
.live-dot i { width: 7px; height: 7px; border-radius: 50%; background: #16a34a; }
.cbody { padding: 30px 32px 64px; max-width: 1000px; }
.lead-sub { color: #6b7280; margin-bottom: 24px; max-width: 64ch; font-size: 15px; }
.actions-row { display: flex; gap: 10px; align-items: center; }
.btn.edit { background: #16a34a; color: #fff; border: 0; }
.btn.edit:hover { background: #15803d; }
.btn.outline { background: #fff; border: 1px solid #d7dbe0; color: #111827;
   box-shadow: 0 1px 1px #0000000a; }
.btn.outline:hover { background: #f9fafb; }
/* site preview with faux browser chrome */
.siteview { background: #fff; border: 1px solid #e6e9ee; border-radius: 14px;
   overflow: hidden; box-shadow: 0 1px 3px #0f172a0d; }
.browserbar { display: flex; align-items: center; gap: 10px; padding: 11px 14px;
   border-bottom: 1px solid #edeff2; background: #fbfbfc; }
.browserbar .dots { display: flex; gap: 6px; }
.browserbar .dots span { width: 11px; height: 11px; border-radius: 50%; background: #e2e5ea; }
.browserbar .addr { flex: 1; max-width: 320px; margin: 0 auto; background: #f1f3f5;
   border-radius: 7px; padding: 6px 12px; font-size: 12.5px; color: #8a94a1;
   text-align: center; }
.siteview .frame { position: relative; height: 440px; background: #fff; overflow: hidden; }
.siteview .frame iframe { position: absolute; top: 0; left: 0; width: 1180px;
   height: 1500px; border: 0; transform: scale(.847); transform-origin: top left; }
.siteview .bar { display: flex; gap: 10px; padding: 16px; border-top: 1px solid #edeff2;
   flex-wrap: wrap; }
/* changes section */
.change-card { background: #fff; border: 1px solid #e6e9ee; border-radius: 12px;
   padding: 22px; margin-bottom: 16px; box-shadow: 0 1px 2px #0f172a08; }
.change-card h3 { font-size: 16px; margin-bottom: 6px; font-weight: 650; }
.change-card p { color: #6b7280; font-size: 14px; margin-bottom: 14px; max-width: 60ch; }
.change-card textarea { width: 100%; padding: 12px 14px; border: 1px solid #d7dbe0;
   border-radius: 9px; font: inherit; resize: vertical; margin-bottom: 12px; }
.change-card textarea:focus { outline: none; border-color: #16a34a;
   box-shadow: 0 0 0 3px #16a34a1f; }
/* go-live steps */
.steps { list-style: none; background: #fff; border: 1px solid #e6e9ee;
   border-radius: 14px; padding: 4px 20px; box-shadow: 0 1px 2px #0f172a08; }
.step { display: flex; gap: 15px; padding: 18px 0; align-items: center;
   border-bottom: 1px solid #f1f3f5; }
.step:last-child { border-bottom: 0; }
.step .marker { flex: none; width: 32px; height: 32px; border-radius: 50%;
   display: flex; align-items: center; justify-content: center; font-weight: 700;
   font-size: 14px; }
.step.done .marker { background: #16a34a; color: #fff; }
.step.now .marker { background: #111827; color: #fff; }
.step.next .marker { background: #eef1f4; color: #9aa3af; }
.step .line { flex: 1; }
.step .line h3 { font-size: 15.5px; font-weight: 600; }
.step .line p { color: #6b7280; font-size: 13.5px; }
.step .tag { flex: none; font-size: 11.5px; font-weight: 600; padding: 5px 11px;
   border-radius: 999px; }
.step.done .tag { background: #f0fdf4; color: #15803d; }
.step.now .tag { background: #eef2f6; color: #334155; }
.step.next .tag { background: #f4f5f7; color: #9aa3af; }
.soon { background: #fff; border: 1px dashed #d7dbe0; border-radius: 12px;
   padding: 44px 32px; color: #6b7280; text-align: center; max-width: 56ch;
   box-shadow: 0 1px 2px #0f172a06; }
@media (max-width: 720px) {
  .console { grid-template-columns: 1fr; }
  .side { position: static; height: auto; }
  .side nav { flex-direction: row; flex-wrap: wrap; }
}
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


# --------------------------------------------------------------------------
# The console shell (left-nav dashboard) shown once a design is chosen
# --------------------------------------------------------------------------

# Clean line icons (Lucide), stroked with currentColor.
def _svg(paths: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')


_ICONS = {
    "site": _svg('<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
                 '<path d="M9 22V12h6v10"/>'),
    "changes": _svg('<path d="M12 20h9"/>'
                    '<path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>'),
    "design": _svg('<rect width="18" height="18" x="3" y="3" rx="2"/>'
                   '<path d="M3 9h18"/><path d="M9 21V9"/>'),
    "details": _svg('<rect width="8" height="4" x="8" y="2" rx="1"/>'
                    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
                    '<path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>'),
    "golive": _svg('<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>'
                   '<path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
                   '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>'
                   '<path d="M15 12v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>'),
}
_NAV = [("site", "nav_site"), ("changes", "nav_changes"), ("design", "nav_design"),
        ("details", "nav_details"), ("golive", "nav_golive")]
_VIEWS = {k for k, _ in _NAV}


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "•"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _sidebar(lead: Lead, active: str, U: dict) -> str:
    lid = _esc(lead.id)
    items = "".join(
        f'<a class="nav-item{" active" if k == active else ""}" '
        f'href="/c/{lid}?view={k}">{_ICONS[k]}<span>{_esc(U[label])}</span></a>'
        for k, label in _NAV
    )
    return f"""<aside class="side">
  <div class="brand">
    <div class="logo">{_esc(_initials(lead.brief.name))}</div>
    <div class="who"><div class="bn">{_esc(lead.brief.name)}</div>
      <div class="bt">{_esc(U['nav_section'])}</div></div>
  </div>
  <nav>{items}</nav>
  <div class="spacer"></div>
  <div class="foot">{_esc(U['app_footer'])}</div>
</aside>"""


def _console_doc(lang: str, U: dict, body: str) -> str:
    return f"""<!doctype html>
<html lang="{_esc(lang)}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{_esc(U['console_title'])}</title>
<style>{_css()}</style>
</head><body class="app">{body}</body></html>"""


def _console_shell(lead: Lead, active: str, title: str, content: str, lang: str) -> str:
    U = i18n.ui(lang)
    lid = _esc(lead.id)
    head = f"""<header class="chead">
  <h1>{_esc(title)}</h1>
  <div class="actions-row">
    <span class="live-dot"><i></i>{_esc(U['console_live_note'])}</span>
    <a class="btn outline" href="/site/{lid}/" target="_blank"
       rel="noopener">{_esc(U['console_visit'])}</a>
  </div>
</header>"""
    body = (f'<div class="console">{_sidebar(lead, active, U)}'
            f'<main class="content">{head}<div class="cbody">{content}</div>'
            f'</main></div>')
    return _console_doc(lang, U, body)


def _sec_site(lead: Lead, U: dict) -> str:
    lid = _esc(lead.id)
    return f"""<p class="lead-sub">{_esc(U['sec_site_sub'])}</p>
<div class="siteview">
  <div class="browserbar">
    <div class="dots"><span></span><span></span><span></span></div>
    <div class="addr">{_esc(U['console_preview_label'])}</div>
  </div>
  <div class="frame">
    <iframe src="/site/{lid}/" scrolling="no" title="{_esc(lead.brief.name)}"></iframe>
  </div>
  <div class="bar">
    <a class="btn edit" href="/c/{lid}/editor">{_esc(U['console_edit_open'])}</a>
    <a class="btn outline" href="/site/{lid}/" target="_blank"
       rel="noopener">{_esc(U['console_visit'])}</a>
  </div>
</div>"""


def _sec_changes(lead: Lead, U: dict) -> str:
    lid = _esc(lead.id)
    return f"""<div class="change-card">
  <h3>{_esc(U['sec_changes_inline_h'])}</h3>
  <p>{_esc(U['sec_changes_inline_d'])}</p>
  <a class="btn edit" href="/c/{lid}/editor">{_esc(U['console_edit_open'])}</a>
</div>
<div class="change-card">
  <h3>{_esc(U['sec_changes_ask_h'])}</h3>
  <p>{_esc(U['sec_changes_ask_d'])}</p>
  <form method="post" action="/c/{lid}/edit">
    <textarea name="instruction" rows="3" required
              placeholder="{_esc(U['console_edit_ph'])}"></textarea>
    <button class="btn primary" type="submit">{_esc(U['console_edit_btn'])}</button>
  </form>
</div>"""


def _sec_design(lead: Lead, others: list, U: dict) -> str:
    sub = f'<p class="lead-sub">{_esc(U["sec_design_sub"])}</p>'
    if not others:
        return sub
    cards = "".join(
        _variant_card(lead, v.key, v.title, v.blurb, v.accent, False, U)
        for v in others
    )
    return sub + f'<div class="grid">{cards}</div>'


def _sec_details(U: dict) -> str:
    return f'<div class="soon">{_esc(U["sec_details_soon"])}</div>'


def _sec_golive(U: dict) -> str:
    # Static for now: design done, personalising in progress, address + live upcoming.
    rows = [
        ("done", "✓", "step_design_t", "step_design_d", "step_done"),
        ("now", "2", "step_personalise_t", "step_personalise_d", "step_now"),
        ("next", "3", "step_address_t", "step_address_d", "step_next"),
        ("next", "4", "step_live_t", "step_live_d", "step_next"),
    ]
    lis = "".join(
        f"""<li class="step {state}">
    <span class="marker">{mark}</span>
    <div class="line"><h3>{_esc(U[tk])}</h3><p>{_esc(U[dk])}</p></div>
    <span class="tag">{_esc(U[tagk])}</span>
  </li>"""
        for state, mark, tk, dk, tagk in rows
    )
    return f'<p class="lead-sub">{_esc(U["sec_golive_sub"])}</p><ul class="steps">{lis}</ul>'


def render_page(lead: Lead | None, job: Job | None, lang: str,
                view: str = "site") -> str:
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
    cv = job.variant(chosen) if chosen else None

    # Chosen + live → the full console (left-nav dashboard).
    if cv is not None:
        active = view if view in _VIEWS else "site"
        others = [v for v in job.variants if v.key != chosen]
        if active == "changes":
            title, content = U["sec_changes_h"], _sec_changes(lead, U)
        elif active == "design":
            title, content = U["sec_design_h"], _sec_design(lead, others, U)
        elif active == "details":
            title, content = U["sec_details_h"], _sec_details(U)
        elif active == "golive":
            title, content = U["sec_golive_h"], _sec_golive(U)
        else:
            title, content = U["sec_site_h"], _sec_site(lead, U)
        return _console_shell(lead, active, title, content, lang)

    # Not chosen yet → the options grid to pick from.
    cards = "".join(
        _variant_card(lead, v.key, v.title, v.blurb, v.accent, False, U)
        for v in job.variants
    )
    body = f"""<section class="hero"><div class="wrap">
  <h1>{_esc(U['console_ready_h'])}</h1>
  <p>{_esc(U['console_ready_sub'])}</p>
</div></section>
<main><div class="wrap"><div class="grid">{cards}</div></div></main>"""
    return _shell(lang, brand, sub, body, refresh=False)
