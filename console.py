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
body.app { background: #f1f5f9; }
.console { display: grid; grid-template-columns: 248px 1fr; min-height: 100vh; }
.side { background: #fff; border-right: 1px solid #e2e8f0; padding: 18px 14px;
   display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; }
.side .brand { font-weight: 800; font-size: 17px; padding: 6px 10px 2px; color: #0f172a; }
.side .brand small { display: block; font-weight: 500; font-size: 12px;
   color: #64748b; margin-top: 3px; }
.side nav { display: flex; flex-direction: column; gap: 3px; margin-top: 16px; }
.nav-item { display: flex; align-items: center; gap: 11px; padding: 10px 12px;
   border-radius: 10px; color: #334155; font-weight: 600; font-size: 15px;
   text-decoration: none; }
.nav-item:hover { background: #f1f5f9; }
.nav-item.active { background: #16a34a14; color: #15803d; }
.nav-item .ic { width: 20px; text-align: center; font-size: 16px; }
.side .spacer { flex: 1; }
.side .foot { border-top: 1px solid #e2e8f0; padding: 12px 10px 2px;
   color: #94a3b8; font-size: 12px; }
.content { min-width: 0; }
.chead { background: #fff; border-bottom: 1px solid #e2e8f0; padding: 15px 32px;
   display: flex; align-items: center; justify-content: space-between;
   position: sticky; top: 0; z-index: 5; }
.chead h1 { font-size: 20px; }
.live-dot { display: inline-flex; align-items: center; gap: 7px; color: #15803d;
   font-weight: 700; font-size: 13px; }
.live-dot i { width: 9px; height: 9px; border-radius: 50%; background: #16a34a; }
.cbody { padding: 28px 32px 64px; max-width: 1040px; }
.lead-sub { color: #64748b; margin-bottom: 22px; max-width: 64ch; }
.actions-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
/* site section */
.siteview { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
   overflow: hidden; }
.siteview .frame { position: relative; height: 470px; background: #f8fafc;
   border-bottom: 1px solid #e2e8f0; overflow: hidden; }
.siteview .frame iframe { position: absolute; top: 0; left: 0; width: 1200px;
   height: 1550px; border: 0; transform: scale(.86); transform-origin: top left; }
.siteview .bar { display: flex; gap: 12px; padding: 16px 18px; flex-wrap: wrap; }
/* changes section */
.change-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
   padding: 22px; margin-bottom: 18px; }
.change-card h3 { font-size: 17px; margin-bottom: 6px; }
.change-card p { color: #64748b; font-size: 14px; margin-bottom: 14px; max-width: 60ch; }
.change-card textarea { width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1;
   border-radius: 10px; font: inherit; resize: vertical; margin-bottom: 12px; }
.change-card textarea:focus { outline: none; border-color: #2563eb; }
/* go-live steps */
.steps { list-style: none; }
.step { display: flex; gap: 16px; padding: 18px 4px; align-items: center;
   border-bottom: 1px solid #eef2f6; }
.step:last-child { border-bottom: 0; }
.step .marker { flex: none; width: 34px; height: 34px; border-radius: 50%;
   display: flex; align-items: center; justify-content: center; font-weight: 700; }
.step.done .marker { background: #16a34a; color: #fff; }
.step.now .marker { background: #2563eb; color: #fff; }
.step.next .marker { background: #e2e8f0; color: #94a3b8; }
.step .line { flex: 1; }
.step .line h3 { font-size: 16px; }
.step .line p { color: #64748b; font-size: 14px; }
.step .tag { flex: none; font-size: 12px; font-weight: 700; padding: 5px 11px;
   border-radius: 999px; }
.step.done .tag { background: #16a34a14; color: #15803d; }
.step.now .tag { background: #2563eb14; color: #1d4ed8; }
.step.next .tag { background: #f1f5f9; color: #94a3b8; }
.soon { background: #fff; border: 1px dashed #cbd5e1; border-radius: 14px;
   padding: 40px 32px; color: #64748b; text-align: center; max-width: 60ch; }
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

_NAV = [
    ("site", "🏠", "nav_site"),
    ("changes", "✏️", "nav_changes"),
    ("design", "🎨", "nav_design"),
    ("details", "🏷️", "nav_details"),
    ("golive", "🚀", "nav_golive"),
]
_VIEWS = {k for k, _, _ in _NAV}


def _sidebar(lead: Lead, active: str, U: dict) -> str:
    lid = _esc(lead.id)
    items = "".join(
        f'<a class="nav-item{" active" if k == active else ""}" '
        f'href="/c/{lid}?view={k}"><span class="ic">{ic}</span>{_esc(U[label])}</a>'
        for k, ic, label in _NAV
    )
    return f"""<aside class="side">
  <div class="brand">{_esc(lead.brief.name)}<small>{_esc(U['nav_section'])}</small></div>
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
  <div class="frame">
    <iframe src="/site/{lid}/" scrolling="no" title="{_esc(lead.brief.name)}"></iframe>
  </div>
  <div class="bar">
    <a class="btn big edit" style="width:auto" href="/c/{lid}/editor">{_esc(U['console_edit_open'])}</a>
    <a class="btn big outline" style="width:auto" href="/site/{lid}/" target="_blank"
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
