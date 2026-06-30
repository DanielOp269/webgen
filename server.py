"""Zero-dependency local web server for webgen.

Routes
  GET  /                          -> the homepage + questionnaire + contact UI
  GET  /api/schema                -> the questions (frontend renders the form)
  POST /api/submit  {answers,contact} -> {ok, lead_id}; stores the lead

The customer app captures leads (brief + contact); it no longer generates sites
itself — that happens separately via our own API, fed from the stored leads.

All bodies are UTF-8; only ASCII goes in headers (http.server uses Latin-1 there).
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import i18n
from .brief import Brief, QUESTIONS
from .leads import Contact, LeadStore

_STATIC = os.path.join(os.path.dirname(__file__), "static")
STORE = LeadStore()


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
                "languages": i18n.LANG_NAMES,
            })
        self._json(404, {"error": "not found"})

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


def serve(port: int = 8770) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"webgen running — open http://127.0.0.1:{port}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
