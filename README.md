# webgen

A near-"zero-human" service that sells **AI-generated websites**. A small-business
owner answers a short questionnaire; we generate one or more finished website
designs; they review, pick one, it goes live; and they can edit it themselves in
plain language — all without ever touching a file.

End-to-end:

```
Marketing funnel  →  captures a Lead (brief + contact)              [web server]
Worker            →  turns each Lead into a generated website        [separate process]
Customer console  →  owner reviews options, picks one, goes live     [web server]
Inline editing    →  edit-what-you-see + AI "make changes"           [web server + worker]
```

Two long-running processes share `data/` on disk:

- **the web server** (`--serve`) — the funnel, the console, and hosting the live sites.
- **the worker** (`--worker`) — the slow/fragile generation + edits, decoupled so a
  wedged browser can't take down lead capture.

## Requirements

- **Python 3.9+**, standard library only for the core (funnel, console, template
  engine — no `pip`).
- **Playwright** — the one real dependency, needed *only* for the engine that drives
  claude.ai in a real browser. See `requirements.txt`; install into a `.venv`. The
  offline template engine needs nothing.
- The landing page loads GSAP / ScrollTrigger / Lenis from a CDN for its animations
  (degrades gracefully to a static page offline).

**Language:** German-first (`i18n.DEFAULT_LANG = "de"`, our target audience). English
is still served to browsers that request it (Accept-Language) or via `?lang=en`.

## Run it

```bash
# the web server (funnel + console + live-site hosting)
python3 -m webgen --serve --port 8770          # http://127.0.0.1:8770

# the generation worker — choose an engine:
python3 -m webgen --worker                      # offline template engine (no install)
WEBGEN_ENGINE=browser .venv/bin/python -m webgen --worker   # real claude.ai sites
python3 -m webgen --worker --once               # one pass then exit (testing)
```

One-time setup for the **browser** engine:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium           # + `install-deps chromium` on Linux
.venv/bin/python browser.py login               # log into claude.ai once (persistent profile)
```

Environment flags: `WEBGEN_ENGINE=browser|template`, `WEBGEN_HEADLESS=1` (headless
browser — prefer headful under Xvfb on a server), `WEBGEN_DEV=1` (enables `/dev`
one-click demo-lead seeding so you don't hand-fill the questionnaire).

## The customer journey

```
1. Funnel    Landing (scrollytelling) → Brief (3-chapter accordion) → Contact → Thank-you
             → a Lead is saved to data/leads/
2. Worker    picks up the lead → generates a site (a Job) → data/jobs/
3. Console   /c/<lead_id> → review the option(s), "Choose this one" → live at /site/<lead_id>/
4. Edit      inline "edit-what-you-see" (change text, upload photos) and a plain-language
             "make changes" box (an AI edit sent as a follow-up to the same claude.ai chat)
```

The 3-chapter brief accordion: **About you → Your website → The design**. Filling a
category stamps a green *Erledigt / Done* badge and auto-scrolls to the next.

## Modules

```
# Funnel (lead capture)
static/index.html  Entire front end: landing + 3-chapter brief accordion + contact + thank-you
brief.py           Questionnaire structure (QUESTIONS) + Brief (validated answers)
leads.py           Contact + Lead + LeadStore (one JSON per lead under data/leads/)

# Generation
worker.py          `--worker`: polls leads, runs generation, applies pending edits
agent.py           Job / Variant / JobStore (jobs under data/jobs/, mtime-aware cross-process sync)
generator.py       Generator seam: TemplateGenerator (offline) | BrowserGenerator (claude.ai)
render.py          The offline template engine (a Direction → full HTML pages)
browser.py         Playwright automation of claude.ai (persistent login, generate, send_edit)
editor.py          Editor seam: BrowserEditor (AI edit via the same chat) | StubEditor (offline)

# Console + hosting + editing
server.py          http.server: funnel API + console + live-site hosting + editor routes
console.py         The customer console page (/c/<lead_id>): pending / ready / chosen, dashboard
siteedit.py        The inline "edit-what-you-see" layer injected into the served site
uploads.py         Customer photo uploads (data/uploads/<lead_id>/, type-allowlisted, 8 MB cap)
devseed.py         WEBGEN_DEV demo-lead seeding

# Shared
i18n.py            ALL human text (funnel UI, landing, brief, console, editor, generated-site copy), EN + DE
```

## Key routes

```
GET  /                    the funnel (landing → brief → contact)
GET  /api/schema?lang=    localized questionnaire schema (the frontend renders it)
POST /api/submit          create a Lead {answers, contact}
GET  /c/<lead>            the customer console
POST /c/<lead>/choose     pick a variant
GET  /c/<lead>/editor     the chosen site with the inline editor
POST /c/<lead>/save-site  save inline edits    POST /c/<lead>/upload  a photo
POST /c/<lead>/edit       queue a plain-language AI change
GET  /site/<lead>/        the customer's live website (their chosen variant)
```

## Where to edit what

- Funnel look/animations, brief accordion, contact → `static/index.html`
- Any human text (keep **EN + DE** in sync; HTTP headers stay ASCII) → `i18n.py`
- Brief questions → `brief.py` (structure) + `i18n.py` (labels / options / groups / chapters)
- Generation engines → `generator.py` / `render.py` / `browser.py`; edit engines → `editor.py`
- Console look/flow → `console.py`; the inline editor layer → `siteedit.py`
- Routes → `server.py`

> Files use `from __future__ import annotations` because Python 3.9 evaluates
> `X | None` type hints at runtime.

## Security note (MVP)

Access to a customer's console, live site, editing, and uploads is currently guarded
only by the **unguessable `lead_id` in the URL**, and the server binds `127.0.0.1`.
Before this faces the public internet it needs real per-lead auth (magic-link / token)
— especially since the **write** routes (save-site, upload, edit) run on that same
token. Browser automation of claude.ai is a known ToS gray area (see `PROJECT_NOTES.md`).

## Adding a language

Add one entry to each of `UI` / `Q` / `OPTIONS` / `GROUPS` / `CHAPTERS` / `SITE` /
`LANG_NAMES` in `i18n.py`, and add the code to `LANGS`. Choice *values* are stable,
language-independent keys (`home`, `modern`, `warm`); labels live in `i18n.py`, so
backend logic never branches on display text.

## Collaborating

`main` is protected — changes land via a branch + pull request the other person
approves. See `CONTRIBUTING.md`. Deeper docs: `CLAUDE.md` (repo guide for Claude Code)
and `PROJECT_NOTES.md` (product vision + roadmap).

```bash
git checkout main && git pull          # start from the latest
git checkout -b my-feature             # your own branch
# work, commit, push, then open a PR
```

> Tip: don't merge a PR with `--delete-branch` if another PR is *stacked* on its
> branch — deleting the base branch closes the stacked PR.
