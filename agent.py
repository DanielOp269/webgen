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


@dataclass
class Task:
    label: str
    status: str = "pending"             # pending | running | done


class Job:
    """One generation run. Owns the task list, progress, and resulting variants."""

    def __init__(self, brief: Brief, generator: Generator, n: int = 3):
        self.id = uuid.uuid4().hex[:12]
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
                with self._lock:
                    self.variants.append(Variant(
                        key=d.key, title=title, blurb=blurb, accent=d.accent,
                        files=files, pages=list(self.brief.pages),
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

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()

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
        self._lock = threading.Lock()
        self._load_all()

    def _path(self, job_id: str) -> str:
        return os.path.join(self.data_dir, job_id + ".json")

    def _load_all(self) -> None:
        for fn in sorted(os.listdir(self.data_dir)):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.data_dir, fn), encoding="utf-8") as fh:
                    job = Job.restore(json.load(fh))
                self._jobs[job.id] = job
            except Exception:                   # skip corrupt/old files, keep serving
                continue

    def _save(self, job: Job) -> None:
        # Atomic write so a crash mid-write never leaves a half file.
        tmp = self._path(job.id) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(job.to_dict(), fh)
        os.replace(tmp, self._path(job.id))

    def create(self, brief: Brief, generator: Generator | None = None, n: int = 3) -> Job:
        job = Job(brief, generator or default_generator(), n=n)
        job.on_done = self._save                # persist when the run finishes
        with self._lock:
            self._jobs[job.id] = job
        job.start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)
