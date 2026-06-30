# How we work together

The goal: **`main` is always working code, and neither of us can overwrite the
other's work.** We get that by never committing straight to `main` — every
change goes through a branch and a pull request (PR).

## The cycle

```bash
git checkout main                 # 1. start from main
git pull                          # 2. get the latest shared state
git checkout -b short-task-name   # 3. make YOUR branch for this task

# ...do the work, commit as you go...
git add -A && git commit -m "Describe what changed"

git push -u origin short-task-name   # 4. push your branch
```

Then on GitHub: **open a Pull Request → the other person reviews → Merge.**
After it merges, go back to step 1 for your next task.

Your partner does the same on *their own* branch at the same time. You're never
writing to the same branch simultaneously, so you can't clobber each other.

## Rules on `main` (enforced by GitHub)

- ❌ No direct pushes to `main` — you must open a PR.
- ✅ A PR needs **1 approval** from the other person before it can merge.
- ❌ No force-pushes or deleting `main`.

## Habits that prevent conflicts

1. **`git pull` on `main` before branching** — always start from the latest.
2. **Small, frequent PRs** beat one giant PR — less to conflict, faster to review.
3. **Divide the files.** Rough split so we rarely touch the same lines:
   - looks of generated sites → `render.py`
   - the app UI → `static/index.html`
   - all human text → `i18n.py`
   - questions → `brief.py`
   - server / jobs / AI wiring → `server.py`, `agent.py`, `generator.py`
   A quick "I'm in i18n today" message avoids most collisions.
4. **Commit only your own work** — don't `git add` files you didn't mean to touch.

## Merge conflicts are normal

If we both edited the same lines, a PR (or `git pull`) will report a *conflict*.
Git marks both versions and asks you to pick — it never destroys anything, and
the old code is always recoverable in history. Resolve it, commit, push.

## Running it

```bash
python3 -m webgen --serve --port 8770   # then open http://127.0.0.1:8770
```
