"""Captured leads: a customer's brief plus how to reach them.

The customer app no longer generates sites itself — it collects a Brief (the
questionnaire answers) and a Contact (name/email/phone/message) and stores them
as a Lead for us to act on. Generation happens separately, via our own API,
fed from these leads.

Persistence mirrors agent.JobStore: one JSON file per lead under data/leads/,
written atomically, reloaded on startup. No threads, no generation — a lead is
just saved on submit.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field

from .brief import Brief


@dataclass
class Contact:
    """How to reach the customer. name + email required; the rest optional."""

    name: str
    email: str
    phone: str = ""
    message: str = ""

    @classmethod
    def from_input(cls, data: dict, lang: str = "en") -> "Contact":
        """Validate raw form input; raise ValueError (localized) on problems."""
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip()
        message = (data.get("message") or "").strip()

        missing = []
        if not name:
            missing.append("Name")
        if not email:
            missing.append("E-Mail" if lang == "de" else "Email")
        if missing:
            prefix = "Bitte ausfüllen: " if lang == "de" else "Please fill in: "
            raise ValueError(prefix + ", ".join(missing))

        # Deliberately lenient: one "@" with a dotted domain is enough. The real
        # check is whether we can reach the person, which only a reply confirms.
        domain = email.rsplit("@", 1)[-1] if "@" in email else ""
        if "@" not in email or "." not in domain:
            raise ValueError("Bitte eine gültige E-Mail-Adresse angeben."
                             if lang == "de"
                             else "Please enter a valid email address.")

        return cls(name=name, email=email, phone=phone, message=message)


@dataclass
class Lead:
    """One submission: the brief, the contact, and when it arrived."""

    id: str
    created: float
    brief: Brief
    contact: Contact

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created": self.created,
            "brief": asdict(self.brief),
            "contact": asdict(self.contact),
        }

    @classmethod
    def restore(cls, data: dict) -> "Lead":
        return cls(
            id=data["id"],
            created=data.get("created", 0.0),
            brief=Brief(**data["brief"]),
            contact=Contact(**data["contact"]),
        )


class LeadStore:
    """Registry of leads, persisted to disk so submissions survive a restart.

    The default data directory lives inside the package so it's stable
    regardless of the working directory.
    """

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(__file__), "data", "leads")
        os.makedirs(self.data_dir, exist_ok=True)
        self._leads: dict[str, Lead] = {}
        self._lock = threading.Lock()
        self._load_all()

    def _path(self, lead_id: str) -> str:
        return os.path.join(self.data_dir, lead_id + ".json")

    def _load_all(self) -> None:
        for fn in sorted(os.listdir(self.data_dir)):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.data_dir, fn), encoding="utf-8") as fh:
                    lead = Lead.restore(json.load(fh))
                self._leads[lead.id] = lead
            except Exception:               # skip corrupt/old files, keep serving
                continue

    def _save(self, lead: Lead) -> None:
        # Atomic write so a crash mid-write never leaves a half file.
        tmp = self._path(lead.id) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(lead.to_dict(), fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path(lead.id))

    def create(self, brief: Brief, contact: Contact) -> Lead:
        lead = Lead(id=uuid.uuid4().hex[:12], created=time.time(),
                    brief=brief, contact=contact)
        with self._lock:
            self._leads[lead.id] = lead
        self._save(lead)
        return lead

    def get(self, lead_id: str) -> Lead | None:
        with self._lock:
            return self._leads.get(lead_id)

    def all(self) -> list[Lead]:
        """All leads, newest first — for an operator view or export later."""
        with self._lock:
            return sorted(self._leads.values(), key=lambda l: l.created, reverse=True)
