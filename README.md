# webgen

A **lead-capture funnel** for a website-building service. A visitor lands on a
marketing homepage, answers a short **brief** (a guided, one-question-at-a-time
questionnaire), leaves their **contact details**, and the submission is saved as
a **lead** for the team to act on.

The actual website generation is **not** done by this app — it happens
separately, via our own API, fed from the stored leads. The generation engine
(`render.py` / `generator.py` / `agent.py`) still lives in the repo as the basis
for that separate service, but it is **not wired into the customer app**.

Built with the **Python standard library only** on the server — no pip, no Node.
The landing page loads GSAP, ScrollTrigger and Lenis from a CDN for its
scroll animations (and degrades gracefully to a static page if they don't load).

## Requirements

- Python 3.9+ (developed on macOS system Python, `/usr/bin/python3`)
- No `pip install`. An internet connection is only needed for the landing-page
  animation libraries (CDN); everything else works offline.

## Run it

```bash
# from the repo root
python3 -m webgen --serve --port 8770
# then open http://127.0.0.1:8770
```

## The customer journey

```
Homepage (Apple-style scrollytelling landing)
  └─ Hero → How it works (1·2·3) → Showcase → Get started → Stats
Brief        guided wizard, one question per screen, progress bar
Contact      name + email (required), phone + message (optional)
Thank-you    confirmation; the lead is saved to data/leads/
```

Each lead is written as one JSON file under `data/leads/` (gitignored),
containing the full brief plus the contact details.

## How it fits together

```
brief.py      Questionnaire schema = single source of truth (frontend renders from /api/schema)
i18n.py       ALL human-facing text (app UI + landing copy + generated-site copy), per language (EN + DE)
leads.py      Contact + Lead + LeadStore — persists each submission to data/leads/ (atomic write, reload on startup)
server.py     http.server endpoints: GET / , GET /api/schema , POST /api/submit
static/index.html   The whole front end in one file: landing + brief wizard + contact + thank-you (HTML/CSS/JS)

# Generation engine — kept for the separate API, NOT used by the customer app:
render.py     Turns a Brief into site directions (modern / bold / elegant)
generator.py  Pluggable Generator seam (template engine now; Claude API can drop in later)
agent.py      Job + task list + threaded run + JobStore
```

### Where to edit what

- **The whole front end** (landing look + animations, brief wizard, contact form)
  → `static/index.html`
- **Any human text** → `i18n.py` (keep EN + DE in sync; HTTP headers stay ASCII)
- **Brief questions** → `brief.py` (structure) + `i18n.py` (labels/options)
- **Lead shape / where leads are stored** → `leads.py`
- **Routes** → `server.py`
- **The future generation engine** → `render.py` / `generator.py` / `agent.py`

> Files use `from __future__ import annotations` because Python 3.9 evaluates
> `X | None` type hints at runtime.

### The landing page (static/index.html)

A single self-contained file. Notable pieces:

- Sections are `.lp-*`; the brief/contact/thank-you steps are `.step` panels
  toggled by `show(name)` in JS (only one visible at a time).
- Animations use GSAP + ScrollTrigger, with Lenis for smooth scrolling, loaded
  via CDN. They are **enhancement only** — every element uses `gsap.from` (final
  state visible), so if the CDN is unreachable or the user prefers reduced
  motion, the page still shows all content and the funnel still works.
- The brief is a wizard: all fields render as `.qslide`s but only one shows at a
  time; `showQuestion` / `nextQuestion` / `prevQuestion` drive it; the progress
  label comes from the `wiz_count` i18n string.

## Adding a language

Extend the `UI`, `Q`, `OPTIONS`, `SITE`, and `LANG_NAMES` tables in `i18n.py`.
Question/option *values* are stable keys (`home`, `modern`, `friendly`); the
labels live in `i18n.py`, so backend logic stays language-independent.

## Collaborating

`main` is protected — changes land via a branch + pull request that the other
person approves. See `CONTRIBUTING.md` for the full workflow. In short:

```bash
git checkout main && git pull          # start from the latest
git checkout -b my-feature             # your own branch
# ...work, commit...
git push -u origin my-feature          # then open a PR on GitHub
```
