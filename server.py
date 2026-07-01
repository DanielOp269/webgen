"""Zero-dependency local web server for webgen.

Routes
  GET  /                          -> the homepage + questionnaire + contact UI
  GET  /api/schema                -> the questions (frontend renders the form)
  POST /api/submit  {answers,contact} -> {ok, lead_id}; stores the lead

The customer app captures leads (brief + contact); it no longer generates sites
itself — that happens separately via our own API, fed from the stored leads.

All bodies are UTF-8; only ASCII goes in headers (http.server uses Latin-1 there).
"""

import io
import json
import os
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import console, i18n
from .agent import JobStore
from .brief import Brief, QUESTIONS
from .leads import Contact, LeadStore

_STATIC = os.path.join(os.path.dirname(__file__), "static")
STORE = LeadStore()
JOBS = JobStore()               # finished jobs written by the worker (read fresh per request)


class Handler(BaseHTTPRequestHandler):
    server_version = "webgen/0.1"

    # -- helpers ------------------------------------------------------------

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _html(self, code: int, text: str) -> None:
        self._send(code, text.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, fmt, *args):  # quieter console
        pass

    def _lang(self, query: str) -> str:
        """Resolve the UI language: explicit ?lang= wins, else Accept-Language."""
        q = parse_qs(query)
        if q.get("lang"):
            return i18n.norm_lang(q["lang"][0])
        return i18n.from_accept_language(self.headers.get("Accept-Language"))

    # -- GET ----------------------------------------------------------------

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/" or path == "/index.html":
            return self._serve_file(os.path.join(_STATIC, "index.html"),
                                    "text/html; charset=utf-8")
        if path == "/api/schema":
            lang = self._lang(urlsplit(self.path).query)
            return self._json(200, {
                "lang": lang,
                "ui": i18n.ui(lang),
                "questions": i18n.localized_questions(QUESTIONS, lang),
                "chapters": i18n.chapters_list(lang),
                "languages": i18n.LANG_NAMES,
            })
        if path == "/c" or path.startswith("/c/"):
            return self._console(path)
        if path == "/site" or path.startswith("/site/"):
            return self._live_site(path)
        self._json(404, {"error": "not found"})

    # -- the customer's live website ----------------------------------------

    def _live_site(self, path: str):
        """Public hosting of a customer's chosen site at /site/<lead_id>/.

        Serves the variant the customer picked in the console (free for now;
        later a paywall gates the choose → live transition). Real hosting /
        a custom domain swap in behind this same route later.
        """
        parts = path.strip("/").split("/")        # ["site", lead_id, <file>]
        if len(parts) < 2 or not parts[1]:
            return self._json(404, {"error": "not found"})
        lead_id = parts[1]

        # Relative links in the generated pages (about.html, …) only resolve if
        # the base path ends in a slash — redirect /site/<id> → /site/<id>/.
        if len(parts) == 2 and not path.endswith("/"):
            self.send_response(308)
            self.send_header("Location", f"/site/{lead_id}/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        job = JOBS.for_lead(lead_id)
        if not job or not job.chosen:
            return self._json(404, {"error": "not found"})
        variant = job.variant(job.chosen)
        if variant is None:
            return self._json(404, {"error": "not found"})
        fname = parts[2] if len(parts) >= 3 and parts[2] else "index.html"
        body = variant.files.get(fname)
        if body is None:
            return self._json(404, {"error": "not found"})
        self._html(200, body)

    # -- customer console ---------------------------------------------------

    def _console(self, path: str):
        """Routes under /c/<lead_id>: the page, per-variant preview, and zip."""
        parts = path.strip("/").split("/")        # ["c", lead_id, ...]
        if len(parts) < 2 or not parts[1]:
            return self._json(404, {"error": "not found"})
        lead_id = parts[1]
        lead = STORE.get(lead_id)
        job = JOBS.for_lead(lead_id) if lead else None
        lang = lead.brief.lang if lead else i18n.from_accept_language(
            self.headers.get("Accept-Language"))

        # /c/<lead_id>  → the console page (states: pending / ready / error)
        if len(parts) == 2:
            code = 200 if lead else 404
            return self._html(code, console.render_page(lead, job, lang))

        # everything below needs a finished variant to serve
        variant = None
        if len(parts) >= 4 and parts[2] == "v" and job:
            v_key = parts[3][:-4] if parts[3].endswith(".zip") else parts[3]
            variant = job.variant(v_key)
        if variant is None:
            return self._json(404, {"error": "not found"})

        # /c/<lead_id>/v/<key>.zip  → download all files for this option
        if len(parts) == 4 and parts[3].endswith(".zip"):
            return self._variant_zip(lead, variant)

        # /c/<lead_id>/v/<key>/site[/<file>]  → serve a rendered file for preview
        if len(parts) >= 5 and parts[4] == "site":
            fname = parts[5] if len(parts) >= 6 and parts[5] else "index.html"
            body = variant.files.get(fname)
            if body is None:
                return self._json(404, {"error": "not found"})
            return self._html(200, body)

        return self._json(404, {"error": "not found"})

    def _variant_zip(self, lead, variant):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, html_text in variant.files.items():
                zf.writestr(fname, html_text)
        data = buf.getvalue()
        # ASCII-only filename in the header (http.server encodes headers as Latin-1).
        stem = "".join(c if c.isalnum() else "-" for c in lead.brief.name).strip("-")
        name = f"{stem or 'website'}-{variant.key}.zip"
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def _serve_file(self, fpath: str, ctype: str):
        try:
            with open(fpath, "rb") as fh:
                self._send(200, fh.read(), ctype)
        except OSError:
            self._json(404, {"error": "not found"})

    # -- POST ---------------------------------------------------------------

    def do_POST(self):
        path = urlsplit(self.path).path
        if path.startswith("/c/") and path.endswith("/choose"):
            return self._console_choose(path)
        if path.startswith("/c/") and path.endswith("/edit"):
            return self._console_edit(path)
        if path != "/api/submit":
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            answers = payload.get("answers", {})
            lang = i18n.norm_lang(answers.get("lang") or payload.get("lang"))
            brief = Brief.from_answers(answers)
            contact = Contact.from_input(payload.get("contact", {}), lang)
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:                # noqa: BLE001
            return self._json(400, {"error": f"bad request: {exc}"})
        lead = STORE.create(brief, contact)
        self._json(200, {"ok": True, "lead_id": lead.id})

    def _console_choose(self, path: str):
        """POST /c/<lead_id>/choose {variant} — record the customer's pick."""
        lead_id = path.strip("/").split("/")[1]
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        variant = (form.get("variant") or [""])[0]
        JOBS.set_choice(lead_id, variant)       # None result → still redirect back
        self._redirect(f"/c/{lead_id}")

    def _console_edit(self, path: str):
        """POST /c/<lead_id>/edit {instruction} — queue a plain-language change."""
        lead_id = path.strip("/").split("/")[1]
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        instruction = (form.get("instruction") or [""])[0]
        JOBS.request_edit(lead_id, instruction)  # None (empty/no choice) → just redirect
        self._redirect(f"/c/{lead_id}")

    def _redirect(self, location: str):
        # POST→redirect→GET so a refresh doesn't re-submit.
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()


def serve(port: int = 8770) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"webgen running — open http://127.0.0.1:{port}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
