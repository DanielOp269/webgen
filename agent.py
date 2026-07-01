"""The agent: a job that works off a task list to produce site variants.

A Job holds an explicit, ordered task list (the "list" the agent works off) and
exposes progress so the UI can show it being processed step by step. Jobs run in
a background thread; the server polls `Job.snapshot()`.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field

from . import i18n
from .brief import Brief
from .generator import Generator, default_generator
from .render import Direction, pick_directions


@dataclass
class Variant:
    key: str
    title: str
    blurb: str
    accent: str
    files: dict[str, str]               # filename -> html
    pages: list[str] = field(default_factory=list)
    chat_url: str = ""                  # claude.ai conversation (browser engine) — lets edits reopen it


@dataclass
class Task:
    label: str
    status: str = "pending"             # pending | running | done


class Job:
    """One generation run. Owns the task list, progress, and resulting variants."""

    def __init__(self, brief: Brief, generator: Generator, n: int = 3,
                 lead_id: str | None = None):
        self.id = uuid.uuid4().hex[:12]
        self.lead_id = lead_id          # the Lead this job was generated for (if any)
        self.chosen: str | None = None  # variant key the customer picked (console)
        # Plain-language edit the customer asked for on their live site. Applied
        # asynchronously by the worker to the chosen variant.
        self.edit_status = ""           # "" | pending | applying | done | error
        self.edit_instruction = ""      # the current pending request
        self.edits: list[str] = []      # history of applied instructions
        self.brief = brief
        self.generator = generator
        self.engine_name = generator.name if generator else "?"
        self.n = n
        self.tasks: list[Task] = []
        self.variants: list[Variant] = []
        self.status = "queued"          # queued | running | done | error
        self.error: str | None = None
        self.created = time.time()
        self.on_done = None             # callback(job) fired when run() finishes
        self._lock = threading.Lock()
        # Set only after run() has fully finished AND on_done (persistence) has
        # returned. Waiters must key on this, not on `status`: status flips to
        # "done" before the file is written, so a process that exits on status
        # alone can kill the save mid-write.
        self.done_event = threading.Event()

    # -- task list ----------------------------------------------------------

    def _plan(self, directions: list[Direction]) -> None:
        t = i18n.ui(self.brief.lang)
        with self._lock:
            self.tasks = [Task(t["task_read"])]
            self.tasks.append(Task(t["task_choose"].format(n=len(directions))))
            for d in directions:
                title = i18n.direction_label(d.key, self.brief.lang)[0]
                self.tasks.append(Task(t["task_generate"].format(title=title)))
            self.tasks.append(Task(t["task_package"]))

    def _advance(self, idx: int, status: str) -> None:
        with self._lock:
            if 0 <= idx < len(self.tasks):
                self.tasks[idx].status = status

    # -- execution ----------------------------------------------------------

    def run(self) -> None:
        self.status = "running"
        try:
            directions = pick_directions(self.brief, self.n)
            self._plan(directions)

            self._advance(0, "running")
            _ = self.brief                      # already parsed/validated
            self._advance(0, "done")

            self._advance(1, "running")
            self._advance(1, "done")

            for i, d in enumerate(directions):
                t = 2 + i
                self._advance(t, "running")
                files = self.generator.generate(self.brief, d)
                title, blurb = i18n.direction_label(d.key, self.brief.lang)
                # Reflect the pages actually produced (a browser variant is a
                # single index.html, the template engine emits every brief page).
                pages = self._pages_for(files)
                # Browser engine exposes the conversation it used, so edits can
                # reopen it; other engines leave it blank.
                chat_url = getattr(self.generator, "chat_url", "") or ""
                with self._lock:
                    self.variants.append(Variant(
                        key=d.key, title=title, blurb=blurb, accent=d.accent,
                        files=files, pages=pages or list(self.brief.pages),
                        chat_url=chat_url,
                    ))
                self._advance(t, "done")

            self._advance(len(self.tasks) - 1, "running")
            self._advance(len(self.tasks) - 1, "done")
            self.status = "done"
        except Exception as exc:                # noqa: BLE001 — surface to UI
            self.status = "error"
            self.error = str(exc)
        finally:
            if self.on_done:
                try:
                    self.on_done(self)
                except Exception:               # persistence must never crash a job
                    pass
            self.done_event.set()               # now safe for waiters to proceed

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()

    # -- edits --------------------------------------------------------------

    def _pages_for(self, files: dict[str, str]) -> list[str]:
        """Which brief pages a file set actually contains (home -> index.html)."""
        return [pk for pk in self.brief.pages
                if ("index.html" if pk == "home" else pk + ".html") in files]

    def apply_edit(self, editor) -> None:
        """Apply the pending edit to the chosen variant via an Editor engine."""
        v = self.variant(self.chosen or "")
        if v is None:
            self.edit_status = "error"
            self.error = "no chosen variant to edit"
            return
        instruction = self.edit_instruction
        self.edit_status = "applying"
        try:
            new_files = editor.edit(self.brief, v, instruction)
            if not new_files:
                raise RuntimeError("editor produced no files")
            with self._lock:
                v.files = new_files
                v.pages = self._pages_for(new_files) or v.pages
                self.edits.append(instruction)
                self.edit_instruction = ""
                self.edit_status = "done"
        except Exception as exc:                # noqa: BLE001 — surface to UI
            self.edit_status = "error"
            self.error = str(exc)

    # -- read models for the API -------------------------------------------

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "status": self.status,
                "error": self.error,
                "engine": self.engine_name,
                "tasks": [{"label": t.label, "status": t.status} for t in self.tasks],
                "lang": self.brief.lang,
                "variants": [
                    {
                        "key": v.key,
                        "title": v.title,
                        "blurb": v.blurb,
                        "accent": v.accent,
                        "pages": [
                            {
                                "key": pk,
                                "label": i18n.page_label(pk, self.brief.lang),
                                "file": "index.html" if pk == "home" else pk + ".html",
                            }
                            for pk in v.pages
                        ],
                    }
                    for v in self.variants
                ],
            }

    def variant(self, key: str) -> Variant | None:
        for v in self.variants:
            if v.key == key:
                return v
        return None

    # -- persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        """Full serialization, including rendered files, for disk storage."""
        with self._lock:
            return {
                "id": self.id,
                "lead_id": self.lead_id,
                "chosen": self.chosen,
                "edit_status": self.edit_status,
                "edit_instruction": self.edit_instruction,
                "edits": list(self.edits),
                "status": self.status,
                "error": self.error,
                "engine": self.engine_name,
                "created": self.created,
                "brief": asdict(self.brief),
                "tasks": [{"label": t.label, "status": t.status} for t in self.tasks],
                "variants": [asdict(v) for v in self.variants],
            }

    @classmethod
    def restore(cls, data: dict) -> "Job":
        """Rebuild a finished job from disk (no generator, never re-runs)."""
        job = cls.__new__(cls)
        job.id = data["id"]
        job.lead_id = data.get("lead_id")
        job.chosen = data.get("chosen")
        job.edit_status = data.get("edit_status", "")
        job.edit_instruction = data.get("edit_instruction", "")
        job.edits = list(data.get("edits", []))
        job.brief = Brief(**data["brief"])
        job.generator = None
        job.engine_name = data.get("engine", "?")
        job.n = len(data.get("variants", []))
        job.tasks = [Task(**t) for t in data.get("tasks", [])]
        job.variants = [Variant(**v) for v in data.get("variants", [])]
        job.status = data.get("status", "done")
        job.error = data.get("error")
        job.created = data.get("created", 0.0)
        job.on_done = None
        job._lock = threading.Lock()
        job.done_event = threading.Event()
        job.done_event.set()                    # restored jobs are already persisted
        return job


class JobStore:
    """Registry of jobs, persisted to disk so results survive a restart.

    Live jobs run in memory and are polled directly; finished jobs are written
    as one JSON file each and reloaded on startup. The default data directory
    lives inside the package so it's stable regardless of the working dir.
    """

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(__file__), "data", "jobs")
        os.makedirs(self.data_dir, exist_ok=True)
        self._jobs: dict[str, Job] = {}
        self._mtimes: dict[str, float] = {}     # job id -> file mtime last loaded
        self._lock = threading.Lock()
        self._load_all()

    def _path(self, job_id: str) -> str:
        return os.path.join(self.data_dir, job_id + ".json")

    def _load_file(self, fn: str) -> None:
        """Load one job file into the registry, recording its mtime."""
        path = os.path.join(self.data_dir, fn)
        try:
            mtime = os.path.getmtime(path)
            with open(path, encoding="utf-8") as fh:
                job = Job.restore(json.load(fh))
        except Exception:                       # skip corrupt/half-written files
            return
        with self._lock:
            self._jobs[job.id] = job
            self._mtimes[job.id] = mtime

    def _load_all(self) -> None:
        for fn in sorted(os.listdir(self.data_dir)):
            if fn.endswith(".json"):
                self._load_file(fn)

    def _save(self, job: Job) -> None:
        # Atomic write so a crash mid-write never leaves a half file.
        tmp = self._path(job.id) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(job.to_dict(), fh)
        os.replace(tmp, self._path(job.id))
        with self._lock:                        # don't re-read our own write
            self._jobs[job.id] = job
            self._mtimes[job.id] = os.path.getmtime(self._path(job.id))

    def create(self, brief: Brief, generator: Generator | None = None,
               n: int | None = None, lead_id: str | None = None) -> Job:
        gen = generator or default_generator()
        if n is None:
            n = getattr(gen, "variants", 3)
        job = Job(brief, gen, n=n, lead_id=lead_id)
        job.on_done = self._save                # persist when the run finishes
        with self._lock:
            self._jobs[job.id] = job
        job.start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def reload(self) -> None:
        """Pick up job files written or updated by another process.

        Reloads new files and any whose mtime changed since we last read them,
        so the two processes see each other's writes: the web server sees jobs
        (and edit requests/results) the worker produced, and the worker sees
        edit requests the server saved — all without a restart.
        """
        for fn in sorted(os.listdir(self.data_dir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(self.data_dir, fn)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            with self._lock:
                fresh = self._mtimes.get(fn[:-5]) == mtime
            if not fresh:
                self._load_file(fn)

    def set_choice(self, lead_id: str, variant_key: str) -> Job | None:
        """Record the variant a customer picked in the console; persist it.

        Returns the updated job, or None if there's no finished job for the lead
        or the variant key is unknown (so the caller can 404 cleanly).
        """
        job = self.for_lead(lead_id)
        if not job or job.status != "done" or job.variant(variant_key) is None:
            return None
        with job._lock:
            job.chosen = variant_key
        self._save(job)                         # atomic re-write of the job file
        return job

    def request_edit(self, lead_id: str, instruction: str) -> Job | None:
        """Queue a plain-language edit for a lead's chosen site. Persist it so
        the (separate) worker process picks it up. Returns None if there's no
        finished, chosen job or the instruction is empty."""
        instruction = (instruction or "").strip()
        job = self.for_lead(lead_id)
        if not job or job.status != "done" or not job.chosen or not instruction:
            return None
        with job._lock:
            job.edit_instruction = instruction
            job.edit_status = "pending"
        self._save(job)
        return job

    def apply_pending(self, job: Job, editor) -> Job:
        """Apply a job's pending edit via an Editor engine, then persist."""
        job.apply_edit(editor)
        self._save(job)
        return job

    def pending_edits(self, refresh: bool = True) -> list[Job]:
        """Jobs with an edit waiting to be applied (read fresh from disk)."""
        if refresh:
            self.reload()
        with self._lock:
            return [j for j in self._jobs.values() if j.edit_status == "pending"]

    def for_lead(self, lead_id: str, refresh: bool = True) -> Job | None:
        """Newest job generated for a lead (read fresh from disk by default)."""
        if refresh:
            self.reload()
        with self._lock:
            jobs = [j for j in self._jobs.values() if j.lead_id == lead_id]
        jobs.sort(key=lambda j: j.created, reverse=True)
        return jobs[0] if jobs else None

    def all(self) -> list[Job]:
        """All jobs (live + restored), newest first."""
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created, reverse=True)
