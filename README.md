# webgen

A small website generator. A customer answers a short **questionnaire**, the
answers become a **Brief**, an "agent" works a task list, and the app produces
**three multi-page static-site variants** the customer can preview and download.

Built with the **Python standard library only** — no pip, no Node, no external
services required to run it.

## Requirements

- Python 3.9+ (developed on macOS system Python, `/usr/bin/python3`)
- Nothing else. No `pip install`.

## Run it

```bash
# from the repo root
python3 -m webgen --serve --port 8770
# then open http://127.0.0.1:8770
```

Walk through the 3 steps: **fill the brief → generate → choose a variant**.
Generated sites and job state are written under `data/jobs/` (gitignored).

## How it fits together

```
brief.py      Questionnaire schema = single source of truth (frontend renders from /api/schema)
i18n.py       ALL human-facing text (UI + generated-site copy), per language (EN + DE)
render.py     Turns a Brief into 3 site directions (modern / bold / elegant)
generator.py  Pluggable Generator seam (template engine now; Claude API can drop in later)
agent.py      Job + task list + threaded run + JobStore (jobs persist to disk)
server.py     http.server endpoints: /api/schema, /api/generate, /api/job/<id>,
              /preview/<id>/<variant>/<file>, /download/<id> (zip)
static/index.html   The 3-step UI (single file: HTML + CSS + JS)
```

### Where to edit what

- **Generated sites' look** → `render.py`
- **The app UI** → `static/index.html`
- **Any human text** → `i18n.py` (keep EN + DE in sync; HTTP headers stay ASCII)
- **Questionnaire questions** → `brief.py`
- **Wiring real AI generation** → `generator.py`

> Files use `from __future__ import annotations` because Python 3.9 evaluates
> `X | None` type hints at runtime.

## Adding a language

Extend the `UI`, `Q`, `OPTIONS`, `SITE`, and `LANG_NAMES` tables in `i18n.py`.
Question/option *values* are stable keys (`home`, `modern`, `friendly`); the
labels live in `i18n.py`, so backend logic stays language-independent.

## Collaborating

```bash
git pull                              # get the latest before you start
git add -A && git commit -m "..."     # commit your changes
git push                              # share them
```

For anything non-trivial, branch first and open a pull request:

```bash
git checkout -b my-feature
# ...work...
git push -u origin my-feature
```
