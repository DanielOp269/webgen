"""Customer-uploaded images for their site.

Stored one folder per lead under data/uploads/<lead_id>/ (gitignored runtime
state, like data/jobs and data/leads). Served back at /c/<lead_id>/img/<name>,
which the edited HTML references — so an uploaded photo works both in the editor
and on the live site (same origin, absolute path).

We generate every filename ourselves (uuid + extension by content-type), so
stored names are always safe; requested names are still sanitised on read.
"""

from __future__ import annotations

import os
import uuid

_ROOT = os.path.join(os.path.dirname(__file__), "data", "uploads")
MAX_BYTES = 8 * 1024 * 1024                 # 8 MB per image

_EXT_BY_TYPE = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/gif": ".gif", "image/webp": ".webp",
}
_TYPE_BY_EXT = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}


def _safe_id(s: str) -> str:
    return "".join(c for c in (s or "") if c.isalnum() or c in "-_")


def _lead_dir(lead_id: str) -> str:
    d = os.path.join(_ROOT, _safe_id(lead_id))
    os.makedirs(d, exist_ok=True)
    return d


def save_image(lead_id: str, data: bytes, content_type: str) -> str | None:
    """Store an uploaded image; return its generated filename, or None if invalid."""
    ext = _EXT_BY_TYPE.get((content_type or "").split(";")[0].strip().lower())
    if not ext or not data or len(data) > MAX_BYTES:
        return None
    name = uuid.uuid4().hex[:16] + ext
    with open(os.path.join(_lead_dir(lead_id), name), "wb") as fh:
        fh.write(data)
    return name


def read_image(lead_id: str, name: str):
    """Return (bytes, content_type) for a stored image, or None."""
    base = os.path.basename(name or "")
    if not base or not all(c.isalnum() or c in "-_." for c in base):
        return None
    path = os.path.join(_ROOT, _safe_id(lead_id), base)
    if not os.path.isfile(path):
        return None
    ctype = _TYPE_BY_EXT.get(os.path.splitext(base)[1].lower(), "application/octet-stream")
    with open(path, "rb") as fh:
        return fh.read(), ctype
