"""Inline "edit-what-you-see" layer for a customer's own website.

The console serves the customer's real chosen site with this thin editing layer
injected: a top toolbar, hover outlines, and click-to-edit text. On Save the
layer serializes the page back to clean HTML (stripping its own toolbar/script/
contenteditable attrs) and POSTs it, so the live site updates.

Deliberately simple and forgiving — the audience is non-technical owners. Only
leaf text is made editable, so they can't accidentally tear out whole sections.
"""

from __future__ import annotations

import html
import json

from . import i18n

# Everything is namespaced with __wg_ so it can be reliably stripped before save.
_LAYER = """
<style id="__wg_style">
  html { scroll-padding-top: 60px; }
  body { margin-top: 60px !important; }
  #__wg_bar { position: fixed; top: 0; left: 0; right: 0; height: 60px;
    z-index: 2147483000; background: #0f172a; color: #fff; display: flex;
    align-items: center; gap: 14px; padding: 0 20px;
    font: 600 15px/1.2 -apple-system, "Segoe UI", Roboto, sans-serif; }
  #__wg_bar .__wg_hint { opacity: .85; font-weight: 500; }
  #__wg_bar .__wg_sp { flex: 1; }
  #__wg_bar button, #__wg_bar a { font: inherit; border: 0; border-radius: 10px;
    padding: 10px 18px; cursor: pointer; text-decoration: none; }
  #__wg_save { background: #16a34a; color: #fff; }
  #__wg_exit { background: #334155; color: #fff; }
  #__wg_bar.embed { background: #fff; color: #111827; border-bottom: 1px solid #edeff2; }
  #__wg_bar.embed .__wg_hint { color: #6b7280; }
  [data-wg-edit]:hover { outline: 2px dashed #3b82f6; outline-offset: 3px;
    cursor: text; border-radius: 2px; }
  [data-wg-edit]:focus { outline: 2px solid #2563eb; outline-offset: 3px; }
  #__wg_toast { position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%);
    background: #16a34a; color: #fff; padding: 13px 22px; border-radius: 12px;
    z-index: 2147483000; font: 600 15px sans-serif; opacity: 0;
    transition: opacity .3s; pointer-events: none; box-shadow: 0 6px 20px #0004; }
</style>
<div id="__wg_bar" class="%%BARMODE%%">
  <span class="__wg_hint">%%HINT%%</span>
  <span class="__wg_sp"></span>
  %%EXIT_BTN%%
  <button id="__wg_save" type="button">%%SAVE%%</button>
</div>
<div id="__wg_toast"></div>
<script id="__wg_script">
(function () {
  var SEL = 'h1,h2,h3,h4,h5,h6,p,a,span,li,button,blockquote,figcaption,' +
            'strong,em,small,label,td,th,dt,dd';
  var BLOCK = 'div,section,article,header,footer,nav,ul,ol,table,form,img,' +
              'h1,h2,h3,h4,h5,h6,p';
  document.querySelectorAll(SEL).forEach(function (el) {
    if (el.closest('#__wg_bar')) return;
    if (el.querySelector(BLOCK)) return;          // only leaf text, not containers
    if (!(el.textContent || '').trim()) return;
    el.setAttribute('data-wg-edit', '1');
    el.setAttribute('contenteditable', 'true');
  });
  // Don't let links/buttons navigate or submit while editing.
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-wg-edit]');
    if (el && (el.tagName === 'A' || el.tagName === 'BUTTON')) e.preventDefault();
  }, true);

  function toast(msg, ok) {
    var t = document.getElementById('__wg_toast');
    t.textContent = msg; t.style.background = ok ? '#16a34a' : '#dc2626';
    t.style.opacity = 1; setTimeout(function () { t.style.opacity = 0; }, 2400);
  }
  document.getElementById('__wg_save').addEventListener('click', function () {
    var clone = document.documentElement.cloneNode(true);
    ['__wg_bar', '__wg_toast', '__wg_style', '__wg_script'].forEach(function (id) {
      var n = clone.querySelector('#' + id); if (n) n.remove();
    });
    clone.querySelectorAll('[data-wg-edit]').forEach(function (el) {
      el.removeAttribute('data-wg-edit'); el.removeAttribute('contenteditable');
    });
    clone.querySelectorAll('style').forEach(function (s) {
      if ((s.textContent || '').indexOf('margin-top: 60px') !== -1) s.remove();
    });
    var html = '<!doctype html>\\n' + clone.outerHTML;
    var btn = document.getElementById('__wg_save');
    btn.disabled = true;
    fetch(%%SAVE_URL%%, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: %%FILE%%, html: html })
    }).then(function (r) { return r.json(); }).then(function (j) {
      toast(j.ok ? %%SAVED%% : %%SAVEFAIL%%, !!j.ok);
    }).catch(function () { toast(%%SAVEFAIL%%, false); })
      .then(function () { btn.disabled = false; });
  });
})();
</script>
"""


def render_editor(page_html: str, lead_id: str, filename: str, lang: str,
                  embed: bool = False) -> str:
    """Inject the editing layer into a served page.

    embed=True is for showing the editor inside the console's "My website" panel:
    a lighter toolbar and no "Done" button (there's no separate page to leave).
    """
    U = i18n.ui(lang)
    layer = _LAYER
    # Raw HTML fragment (built here, not escaped by the loop below).
    exit_btn = ("" if embed else
                f'<a id="__wg_exit" href="/c/{html.escape(lead_id)}">'
                f'{html.escape(U["console_edit_exit"])}</a>')
    layer = (layer.replace("%%EXIT_BTN%%", exit_btn)
                  .replace("%%BARMODE%%", "embed" if embed else ""))
    # Values placed in HTML markup — HTML-escape them.
    for k, v in {
        "%%HINT%%": U["console_edit_hint"],
        "%%SAVE%%": U["console_edit_save"],
    }.items():
        layer = layer.replace(k, html.escape(v, quote=True))
    # Values placed inside JavaScript — JSON-encode so quotes/specials are safe
    # (the copy contains apostrophes, e.g. "couldn't").
    for k, v in {
        "%%SAVED%%": U["console_edit_saved"],
        "%%SAVEFAIL%%": U["console_edit_savefail"],
        "%%SAVE_URL%%": f"/c/{lead_id}/save-site",
        "%%FILE%%": filename,
    }.items():
        layer = layer.replace(k, json.dumps(v))
    # Insert just before </body> so the site's own markup is untouched.
    lower = page_html.lower()
    idx = lower.rfind("</body>")
    if idx == -1:
        return page_html + layer
    return page_html[:idx] + layer + page_html[idx:]
