"""Zero-dependency local web server for webgen.

Routes
  GET  /                              -> the questionnaire UI
  GET  /api/schema                    -> the questions (frontend renders the form)
  POST /api/generate   {answers}      -> {job_id}; starts the agent
  GET  /api/job/<id>                  -> job snapshot (status, task list, variants)
  GET  /preview/<id>/<variant>/<file> -> a rendered page (relative links work)
  GET  /download/<id>/<variant>       -> the variant as a .zip

All bodies are UTF-8; only ASCII goes in headers (http.server uses Latin-1 there).
"""

import io
import json
import os
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import i18n
from .agent import JobStore
from .brief import Brief, QUESTIONS

_STATIC = os.path.join(os.path.dirname(__file__), "static")
STORE = JobStore()


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
        if path.startswith("/api/job/"):
            return self._job(path.rsplit("/", 1)[-1])
        if path.startswith("/preview/"):
            return self._preview(path)
        if path.startswith("/download/"):
            return self._download(path)
        self._json(404, {"error": "not found"})

    def do_HEAD(self):
        self.do_GET()

    def _serve_file(self, fpath: str, ctype: str):
        try:
            with open(fpath, "rb") as fh:
                self._send(200, fh.read(), ctype)
        except OSError:
            self._json(404, {"error": "not found"})

    def _job(self, job_id: str):
        job = STORE.get(job_id)
        if not job:
            return self._json(404, {"error": "unknown job"})
        self._json(200, job.snapshot())

    def _preview(self, path: str):
        # /preview/<id>/<variant>/<file?>
        parts = path.split("/")[2:]
        if len(parts) < 2:
            return self._json(404, {"error": "bad preview path"})
        job_id, vkey = parts[0], parts[1]
        fname = parts[2] if len(parts) > 2 and parts[2] else "index.html"
        job = STORE.get(job_id)
        variant = job.variant(vkey) if job else None
        if not variant:
            return self._json(404, {"error": "unknown variant"})
        page = variant.files.get(fname)
        if page is None:
            return self._json(404, {"error": "unknown page"})
        self._html(200, page)

    def _download(self, path: str):
        parts = path.split("/")[2:]
        if len(parts) < 2:
            return self._json(404, {"error": "bad download path"})
        job_id, vkey = parts[0], parts[1]
        job = STORE.get(job_id)
        variant = job.variant(vkey) if job else None
        if not variant:
            return self._json(404, {"error": "unknown variant"})
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in variant.files.items():
                zf.writestr(fname, content)
        data = buf.getvalue()
        safe = "".join(c for c in (job.brief.name or "site") if c.isalnum()) or "site"
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{safe}-{vkey}.zip"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # -- POST ---------------------------------------------------------------

    def do_POST(self):
        path = urlsplit(self.path).path
        if path != "/api/generate":
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            answers = payload.get("answers", payload)
            brief = Brief.from_answers(answers)
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:                # noqa: BLE001
            return self._json(400, {"error": f"bad request: {exc}"})
        job = STORE.create(brief)
        self._json(200, {"job_id": job.id})


def serve(port: int = 8770) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"webgen running — open http://127.0.0.1:{port}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
