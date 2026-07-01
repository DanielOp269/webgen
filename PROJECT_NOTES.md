# Webgen — Project Notes

> Working doc capturing what we've decided so a session (human or Claude) can start again from here.
> Last updated: 2026-06-30

## The idea
A near-"0 human company" that sells AI-generated websites.

End-to-end flow:
1. An interested lead fills out a **questionnaire** (what their business does, design preferences, must-haves).
2. The submission triggers an **AI agent** that turns the brief into several website options.
3. We **send the lead a few designs** for approval.
4. The lead **picks one and pays**.
5. We then **take that site live** for them.

## Scope — what's OURS vs someone else's
- **OURS:** the **generation engine** — the machine that turns a brief into finished website options.
- **NOT ours:** the **marketing/service site** (where the service is advertised) and the **questionnaire form** on it — another team builds that.
- So we own one box with a clean contract to their side.

## Key decisions made
- **Generation method:** an automation agent ("OpenClaw") **drives claude.ai in a browser** (Claude chat / Artifacts), prompts it with the brief, and we **scrape the resulting Artifact HTML** and **host it ourselves**. (No official "Claude builds websites" API exists — this is browser automation pretending to be a human.)
- **Deployment:** **everything runs on one server** (single VM/LXC, well-suited to Proxmox homelab) — not split across serverless. A persistent logged-in browser session needs a long-running box.
- **Intake is async:** generation takes minutes, so their site POSTs a brief, we ack + queue, and notify when done. Not a blocking request.

## Target architecture (one server)
```
[their marketing site + questionnaire]
        | brief (structured answers)
        v
+------------------------------------------+
| OUR GENERATION ENGINE (one server)       |
| 1. Intake API   receive brief -> queue   |
| 2. Job store    SQLite: queued->done/fail|
| 3. Worker       OpenClaw + headful Chrome:|
|                 login claude.ai (persistent profile)
|                 -> prompt brief -> wait for Artifact
|                 -> extract HTML -> repeat xN variants
| 4. Artifact store  save each variant HTML |
| 5. Preview hosting serve /preview/<job>/<variant>
| 6. Delivery     notify their site         |
| 7. Mini dashboard see queue / stuck / retry|
+------------------------------------------+
        | results (preview URLs + screenshots)
        v
[back to their side -> shown to lead for approval]
```

## Known risk (design around it)
The fragile heart is automating claude.ai:
- No API — relies on a **persistent logged-in Chrome profile** (cookies expire).
- Can break on **claude.ai UI changes**, **Cloudflare/bot checks**, and **account/usage limits**.
- ToS gray area.
- Mitigations: persistent browser profile, **generous retries**, and a **dashboard** so a wedged session surfaces instead of silently eating leads.
Everything around the core (intake, storage, hosting, delivery) is reliable and easy.

## The repo (DanielOp269/webgen)
- Cloned into `~/Desktop/Webgen`, branch `main`, one commit: "Initial commit: webgen website generator."
- It's a **Python** project (we'd assumed Node — glad we checked).
- Files and best-guess roles (NOT yet read in detail):
  - `server.py` — web server / intake
  - `agent.py` — generation agent (likely the OpenClaw/Claude driver)
  - `brief.py` — questionnaire/brief model
  - `generator.py` — orchestrates generation
  - `render.py` — turns output into a hosted site
  - `i18n.py` — translations (sizable; multi-language?)
  - `static/` — assets / generated output
  - `__main__.py` / `__init__.py` — entry point / package

## Update — 2026-06-30 (session 2)

Read the code, then built and validated the generation engine. Where things stand now:

**Confirmed approach:** browser automation of claude.ai (NOT the Claude API). We
drive a persistent logged-in Chromium, prompt it with the brief, and scrape the
HTML out of the reply (asking for a single ```html code block, no Artifact —
much more robust than iframe extraction). Proven end-to-end.

**Beating the "AI template look":** quality is a prompt problem, not a model
problem. A strongly-directed prompt (explicit design POV + a ban on the cliché
AI look + real Google Fonts/Unsplash imagery) plus one self-critique refinement
turn produces genuinely non-generic, sellable single-page sites — automatically.
Validated; we decided we do NOT need a manual "Claude design + handover" route.

**Built this session:**
- `browser.py` — persistent-profile login, the generation flow (send → wait →
  extract), per-direction "aesthetics" library, and a global lock so only one
  browser runs at a time.
- `BrowserGenerator` wired behind the existing `Generator` seam — the
  questionnaire → job → preview/zip flow now produces real Claude sites with
  zero changes to server/agent. Selected via `WEBGEN_ENGINE=browser`.
- Single-page output (one `index.html`); browser jobs default to 1 variant
  (slow + serialized). Brief→prompt mapping is minimal for now (name/industry/
  tone/language); rich questionnaire-field mapping deferred.
- First real dependency: Playwright (in `.venv`, `requirements.txt`).

## Expanded scope & delivery model (decided session 2)

We build the WHOLE customer-facing side, not just generation. Target flow:

```
brief in → generate async (no one waiting) → EMAIL the lead a private link
  → they open their CONSOLE, review the concept(s)
  → they PAY → editing unlocks → they request changes → we regenerate
```

- The current "watch it generate" screen becomes an internal dev/ops view; the
  customer experience is a tokenized per-lead console (magic-link, no password).
- **Edits = AI edits via chat:** the customer describes a change in plain words
  and we send it as a follow-up turn to the SAME claude.ai conversation, which
  revises the whole file. Our browser approach is ideal for this.
- **Implication / next foundational step:** we must persist each job's claude.ai
  conversation (chat URL) so we can reopen it for edits. Right now we open a
  fresh chat each run and discard the URL — that needs to change before/with the
  edit loop.

## Remaining roadmap (rough order)
1. Persist the claude.ai conversation per job + an engine-level `edit()` path.
2. Async + email notification (magic link to the console) on job completion.
3. Customer console (`/c/<token>`): review + preview.
4. Payment (Stripe) gating the edit feature.
5. Edit loop UI → regenerate via chat follow-up.
6. Harden (login-expiry detection, retries, the flaky "is-it-done?" wait) +
   productionize (Proxmox VM + Xvfb, take-live hosting).
