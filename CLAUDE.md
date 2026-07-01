# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

webgen is a near-"zero-human" service that sells AI-generated websites. A small-business owner fills a questionnaire (the **funnel**), a **worker** turns that brief into a finished website, the owner reviews the option(s) in a **console**, picks one, it goes live, and they can edit it in plain language. The whole product lives in this one repo.

Two long-running processes share `data/` on disk: the **web server** (`--serve` — funnel, console, live-site hosting) and the **worker** (`--worker` — the slow/fragile generation + edits, decoupled so a wedged browser can't take down lead capture). Generation runs either offline (deterministic template renderer, `render.py`) or for real by driving **claude.ai in a browser** (`browser.py`, Playwright), selected by `WEBGEN_ENGINE`.

## Running

The core app is stdlib-only (`from __future__ import annotations` keeps it 3.9-compatible). The **generation worker** adds one real dependency — Playwright — for browser automation; everything else still runs with no install.

```sh
# one-time setup for the browser engine
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium       # + `install-deps chromium` on Linux
.venv/bin/python browser.py login           # log into claude.ai once (persistent profile)

# run it
python3 -m webgen --serve                    # web UI at http://127.0.0.1:8770
WEBGEN_ENGINE=browser .venv/bin/python -m webgen --worker   # consume leads, generate
python3 -m webgen --worker --once            # worker: single pass then exit (testing)
```

Run from the *parent* directory of the repo (the package is imported as `webgen`); macOS's case-insensitive FS lets `-m webgen` resolve the `Webgen/` dir. There is no test suite, linter config, or CI.

**Engine selection** (`generator.default_generator()`): `WEBGEN_ENGINE=browser` → real claude.ai generation; `WEBGEN_ENGINE=template` (or unset with no key) → offline template engine; `ANTHROPIC_API_KEY` set → the (still-stubbed) `ClaudeGenerator`. `WEBGEN_HEADLESS=1` runs the browser headless (use headful under Xvfb on a server).

## Architecture

The product is two decoupled halves that share `data/` on disk (both merged to `main`): a **customer funnel + console** (the web server) and a **generation worker**. The funnel captures a Lead; the worker generates a site for it; the console lets the owner review / choose / edit; the chosen site is hosted at `/site/<lead>/`. The funnel + brief UI is owned by Daniel (`DanielOp269`), the engine + console + editor by Philip (`lucasagency`).

The generation path: **lead (brief + contact) → worker → background job → generator → rendered variant(s) → preview/download**. Flat module layout, no subpackages.

- **`browser.py`** — the claude.ai browser-automation engine (Playwright). Owns the persistent logged-in Chromium profile (`browser_profile/`, gitignored — holds your session), the prompt builder (`site_prompt`, with a per-direction `AESTHETICS` library + an anti-"AI template" prompt and a refinement turn), and `generate_html(prompt, refine=...)`. A module-level lock serializes all browser use (only one persistent-profile Chromium can run at once). CLI: `login` / `check` / `gen` / `gen2`.
- **`leads.py`** — `Lead` (Brief + Contact) and `LeadStore` (one JSON per lead under `data/leads/`, atomic write, reload on startup). Adopted from Daniel's branch as the shared input contract; the funnel writes leads, the worker reads them.
- **`worker.py`** — `python -m webgen --worker`. Polls `data/leads/`, generates each lead that has no job yet (linked via `Job.lead_id`), idempotent, serialized one-at-a-time. The separate process that does the slow/fragile generation so a wedged browser can't take down lead capture.

- **`server.py`** — zero-dep HTTP server (`http.server.ThreadingHTTPServer`), bound to `127.0.0.1`. Funnel: `GET /`, `GET /api/schema`, `POST /api/submit` (creates a Lead). Console + hosting: `GET/POST /c/<lead>/…` (page, choose, editor, save-site, upload, img, edit) and `GET /site/<lead>/…` (the chosen live site). Reads jobs fresh from a shared `JobStore` each request (mtime-aware, so it sees the worker's output). Access is guarded only by the unguessable `lead_id` — MVP; needs real per-lead auth before it's public. `console.py`/`siteedit.py`/`uploads.py`/`devseed.py` back these routes.
- **`brief.py`** — `QUESTIONS` (the questionnaire **structure** only: ids, types, and stable option *value keys*) and `Brief` (normalized, validated answers). `Brief.from_answers` validates required fields and returns errors in the answer's language.
- **`agent.py`** — `Job`, `Task`, `Variant`, `JobStore`. A `Job` owns an ordered task list and runs the generation on a daemon thread, advancing task statuses so the UI shows step-by-step progress. `JobStore` persists **finished** jobs to disk as one JSON file each (`data/jobs/<id>.json`, atomic write) and reloads them on startup; restored jobs never re-run (no generator attached). Jobs carry an optional `lead_id` linking back to the `Lead` they were generated for; a variant's `pages` reflects the files actually produced (so a single-page browser site shows no broken page tabs).
- **`generator.py`** — the swap seam. `Generator` is the interface (`generate(brief, direction) -> {filename: html}`, plus a `variants` class attr = default option count). `TemplateGenerator` (offline, 3 multi-page variants), `BrowserGenerator` (real claude.ai via `browser.py`; **single-page** `index.html`, `variants=1` because it's slow + serialized; maps each Direction to a prompt aesthetic), and the stubbed `ClaudeGenerator`. `default_generator()` selects by `WEBGEN_ENGINE`/key (see Running). The seam means new engines need no edits to server/agent/worker.
- **`render.py`** — `TemplateGenerator`'s engine. `Direction` = a self-contained look (palette, fonts, hero style); `DIRECTIONS` holds the built-in set. `pick_directions` chooses which directions a brief gets. `render_site` builds each requested page as a full HTML doc with inlined CSS, via per-page builder functions in `_PAGE_BUILDERS`.
- **`i18n.py`** — all human-readable text for every supported language (UI chrome, question/option labels, generated-site copy). Imports nothing from the package so anything can use it freely.
- **`static/index.html`** — the entire funnel front end (vanilla JS, no build step): an Apple-style scrollytelling landing, the 3-chapter brief **accordion** (fetches `/api/schema`; one category box at a time, each stamps "Erledigt/Done" and auto-scrolls to the next), and the contact + thank-you steps. Posts to `/api/submit`. GSAP/ScrollTrigger/Lenis load from a CDN as enhancement-only (degrades gracefully offline / reduced-motion).

## Conventions that matter

- **Value keys vs. labels.** Choices (`"modern"`, `"home"`, `"friendly"`, direction keys, page keys) are stable, language-independent value keys used throughout the backend. Every human-readable label is looked up in `i18n.py` by that key + `lang`. **Never branch program logic on display text**, and never hardcode user-facing copy outside `i18n.py`. Adding a language = add one entry to each of `UI` / `Q` / `OPTIONS` / `SITE` / `LANG_NAMES`.
- **Language flows from the brief.** `brief.lang` drives the generated site's language; the UI language comes from `?lang=` or `Accept-Language` (`i18n.norm_lang` / `from_accept_language`).
- **Generated HTML is self-contained**: CSS is inlined, fonts degrade to system fonts, internal links use relative filenames (`index.html` for `home`, `<key>.html` otherwise — see `render._filename`) so a downloaded zip works offline. Always escape brief-derived text with `render._esc` (`home`/`page_label` etc.).
- **Headers are ASCII-only** (http.server uses Latin-1 for headers); all bodies are UTF-8.
- **`data/jobs/` is runtime state, not source** — gitignored. Generators are pluggable; keep new engines behind the `Generator` interface so the rest of the pipeline stays unchanged.

## Project context

`PROJECT_NOTES.md` is a living design doc for the broader product vision (async intake, persisted job queue, ops dashboard, the originally-discussed claude.ai browser-automation approach). Read it for *why* before large changes; note the current code is simpler than that target architecture (synchronous in-process jobs, no callback delivery yet).
