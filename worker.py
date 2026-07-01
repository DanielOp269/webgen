"""Generation worker: turn captured Leads into generated sites.

The customer funnel app only *captures* Leads (brief + contact) into
data/leads/. This worker is the separate process that does the slow, fragile
part: it picks up each new Lead and runs it through the generation engine,
producing a Job (the design concept) linked back to that Lead.

Decoupled on purpose — if the browser engine wedges, lead capture keeps working.

    python3 -m webgen --worker            # poll forever
    python3 -m webgen --worker --once     # one pass, then exit (handy for testing)

The engine is chosen by default_generator() (WEBGEN_ENGINE=browser for the real
claude.ai path; the template engine otherwise).
"""

from __future__ import annotations

import time

from .agent import JobStore
from .leads import LeadStore


def pending_leads(leads: LeadStore, jobs: JobStore) -> list:
    """Leads that don't have a generation job yet, oldest first."""
    done = {j.lead_id for j in jobs.all() if j.lead_id}
    return [lead for lead in reversed(leads.all()) if lead.id not in done]


def process_once(leads: LeadStore, jobs: JobStore, *, timeout: float = 900.0) -> int:
    """Generate for every lead without a job yet. Returns how many were handled."""
    todo = pending_leads(leads, jobs)
    for lead in todo:
        print(f"→ generating for lead {lead.id} <{lead.contact.email}> — {lead.brief.name}")
        job = jobs.create(lead.brief, lead_id=lead.id)
        # One at a time: wait for completion (and persistence) before the next.
        # Waiting on done_event — not job.status — guarantees the job file is
        # fully written before we move on or the process exits.
        if not job.done_event.wait(timeout):
            print(f"  ⚠️  lead {lead.id} → job {job.id}: timed out after {timeout:.0f}s")
            continue
        if job.status == "done":
            print(f"  ✅ lead {lead.id} → job {job.id} ({len(job.variants)} variant(s))")
        else:
            print(f"  ⚠️  lead {lead.id} → job {job.id}: status={job.status} error={job.error}")
    return len(todo)


def run(interval: float = 10.0, once: bool = False) -> None:
    leads = LeadStore()
    jobs = JobStore()
    print(f"webgen worker — watching {leads.data_dir}")
    while True:
        try:
            process_once(leads, jobs)
        except Exception as exc:                # never let one failure kill the loop
            print(f"worker error: {exc}")
        if once:
            break
        time.sleep(interval)
