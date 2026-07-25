"""Pure dataclasses for Plastic SCM entities — no Qt, no biome_fm imports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Status codes emitted by cm status
STATUS_LABELS: dict[str, str] = {
    "CO": "checked-out",
    "CH": "changed",
    "AD": "added",
    "PR": "private",
    "LD": "locally-deleted",
    "DE": "deleted",
    "MV": "moved",
    "CP": "copied",
    "IG": "ignored",
}

# Plastic emits dates in locale-dependent formats; try the most common ones
_DATE_FMTS = (
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M:%S %p",  # 12h with AM/PM
)


def parse_date(s: str) -> datetime:
    """Parse Plastic date string. Falls back to epoch on unknown format."""
    s = s.strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.fromtimestamp(0)


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


@dataclass(slots=True)
class PlasticItem:
    status: str   # 2-letter Plastic code: CO, AD, PR, LD, DE, MV, CH, CP
    path: Path

    @property
    def label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)


@dataclass(slots=True)
class Changeset:
    cs_id: int
    date: datetime
    owner: str
    branch: str
    comment: str


@dataclass(slots=True)
class CSDiffFile:
    path: str
    status: str      # "A" | "M" | "D"
    added: int
    removed: int
    diff_text: str


@dataclass(slots=True)
class Branch:
    name: str
    date: datetime
    owner: str
    parent: str = ""


@dataclass(slots=True)
class Label:
    name: str
    changeset: int
    date: datetime


@dataclass(frozen=True)
class Lock:
    path: Path
    owner: str
    branch: str
    status: str = "Locked"   # "Locked" | "Retained"


@dataclass(frozen=True)
class Shelve:
    shelve_id: int
    date: datetime
    owner: str
    comment: str


@dataclass(slots=True)
class Revision:
    rev_id: int       # item revision number ({id})
    cs_id: int        # changeset id ({changesetid})
    date: datetime
    owner: str
    comment: str
    branch: str


@dataclass(slots=True)
class BlameLine:
    line_no: int      # 1-based ({line})
    owner: str
    cs_id: int        # ({changeset})
    date: datetime
    content: str      # raw source line; may contain |


@dataclass(frozen=True)
class Review:
    review_id: int
    status: str       # "Under review" | "Reviewed" | "Rework required"
    assignee: str
    date: datetime
    title: str
    target_cs: int = 0   # populated on create, not from list output


@dataclass(frozen=True)
class ChangelistInfo:
    name: str
    description: str = ""


@dataclass(frozen=True)
class WorkspaceInfo:
    name: str
    server: str
    branch: str
    last_cs: int
    wk_path: Path


@dataclass(frozen=True)
class Xlink:
    path: str       # local relative mount path
    server: str
    repo: str
    branch: str = ""
    cs_id: int = 0


@dataclass(frozen=True)
class Attribute:
    object_spec: str
    name: str
    value: str


@dataclass(frozen=True)
class AclEntry:
    principal: str
    kind: str
    permission: str


@dataclass(frozen=True)
class UserInfo:
    name: str
    email: str = ""


@dataclass(frozen=True)
class GroupInfo:
    name: str
    members: tuple = ()


@dataclass(frozen=True)
class ConfigEntry:
    key: str
    value: str


@dataclass(frozen=True)
class WorkspaceEntry:
    name: str
    path: Path
    server: str


@dataclass(frozen=True)
class RepoEntry:
    name: str
    server: str


@dataclass(frozen=True)
class Trigger:
    trigger_id: str
    name: str
    event: str
    filter: str
    command: str
