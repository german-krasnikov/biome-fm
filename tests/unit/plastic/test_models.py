"""Unit tests for _models.py — PlasticItem, Changeset, Branch, Label, parse_date."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from biome_fm.plastic._models import (
    STATUS_LABELS,
    Branch,
    Changeset,
    Label,
    Lock,
    PlasticItem,
    Shelve,
    parse_date,
)


# ── STATUS_LABELS ─────────────────────────────────────────────────────────────

def test_status_labels_has_nine_entries():
    assert len(STATUS_LABELS) == 9


@pytest.mark.parametrize("code,expected", [
    ("CO", "checked-out"),
    ("CH", "changed"),
    ("AD", "added"),
    ("PR", "private"),
    ("LD", "locally-deleted"),
    ("DE", "deleted"),
    ("MV", "moved"),
    ("CP", "copied"),
    ("IG", "ignored"),
])
def test_status_labels_all_known(code, expected):
    assert STATUS_LABELS[code] == expected


# ── PlasticItem ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("code", STATUS_LABELS)
def test_plastic_item_label_known_codes(code):
    item = PlasticItem(status=code, path=Path("/foo"))
    assert item.label == STATUS_LABELS[code]


def test_plastic_item_label_unknown_returns_code():
    item = PlasticItem(status="XX", path=Path("/foo"))
    assert item.label == "XX"


def test_plastic_item_stores_path():
    p = Path("/workspace/src/file.py")
    item = PlasticItem(status="CO", path=p)
    assert item.path == p


# ── parse_date ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("s,expected", [
    ("07/24/2026 14:30:00",   datetime(2026, 7, 24, 14, 30, 0)),   # MM/DD/YYYY HH:MM:SS
    ("2026-07-24 14:30:00",   datetime(2026, 7, 24, 14, 30, 0)),   # ISO
    ("2026/07/24 14:30:00",   datetime(2026, 7, 24, 14, 30, 0)),   # YYYY/MM/DD
    ("24/07/2026 14:30:00",   datetime(2026, 7, 24, 14, 30, 0)),   # DD/MM/YYYY
    ("07/24/2026 02:30:00 PM", datetime(2026, 7, 24, 14, 30, 0)),  # 12h AM/PM
])
def test_parse_date_known_formats(s, expected):
    assert parse_date(s) == expected


def test_parse_date_strips_whitespace():
    assert parse_date("  2026-07-24 00:00:00  ") == datetime(2026, 7, 24, 0, 0, 0)


def test_parse_date_unknown_format_returns_epoch():
    result = parse_date("not a date at all")
    assert result == datetime.fromtimestamp(0)


def test_parse_date_empty_string_returns_epoch():
    assert parse_date("") == datetime.fromtimestamp(0)


# ── Dataclasses ───────────────────────────────────────────────────────────────

def test_changeset_fields():
    cs = Changeset(cs_id=42, date=datetime(2026, 1, 1), owner="alice", branch="main", comment="fix")
    assert cs.cs_id == 42
    assert cs.owner == "alice"
    assert cs.branch == "main"
    assert cs.comment == "fix"


def test_branch_fields():
    b = Branch(name="/main/task-1", date=datetime(2026, 1, 1), owner="bob")
    assert b.name == "/main/task-1"
    assert b.owner == "bob"


def test_label_fields():
    lbl = Label(name="v1.0", changeset=100, date=datetime(2026, 1, 1))
    assert lbl.name == "v1.0"
    assert lbl.changeset == 100


# ── Shelve ────────────────────────────────────────────────────────────────────

def test_shelve_fields():
    s = Shelve(shelve_id=7, date=datetime(2026, 7, 24), owner="alice", comment="WIP")
    assert s.shelve_id == 7
    assert s.owner == "alice"
    assert s.comment == "WIP"


def test_shelve_is_frozen():
    s = Shelve(shelve_id=1, date=datetime(2026, 1, 1), owner="bob", comment="x")
    try:
        s.shelve_id = 2  # type: ignore[misc]
        assert False, "should have raised"
    except (AttributeError, TypeError):
        pass


def test_shelve_equality():
    d = datetime(2026, 1, 1)
    assert Shelve(1, d, "a", "b") == Shelve(1, d, "a", "b")
    assert Shelve(1, d, "a", "b") != Shelve(2, d, "a", "b")


# ── Lock ──────────────────────────────────────────────────────────────────────

def test_lock_fields():
    lk = Lock(path=Path("/src/foo.cs"), owner="alice", branch="/main")
    assert lk.path == Path("/src/foo.cs")
    assert lk.owner == "alice"
    assert lk.branch == "/main"
    assert lk.status == "Locked"


def test_lock_is_frozen():
    lk = Lock(path=Path("/a.cs"), owner="bob", branch="/main")
    try:
        lk.owner = "eve"  # type: ignore[misc]
        assert False, "should have raised"
    except (AttributeError, TypeError):
        pass


def test_lock_equality():
    p = Path("/a.cs")
    assert Lock(p, "alice", "/main") == Lock(p, "alice", "/main")
    assert Lock(p, "alice", "/main") != Lock(p, "bob", "/main")


# ── Revision ──────────────────────────────────────────────────────────────────

from biome_fm.plastic._models import Revision, BlameLine  # noqa: E402


def test_revision_fields():
    r = Revision(rev_id=7, cs_id=42, date=datetime(2026, 7, 24), owner="alice", comment="fix", branch="/main")
    assert r.rev_id == 7
    assert r.cs_id == 42
    assert r.owner == "alice"
    assert r.comment == "fix"
    assert r.branch == "/main"


def test_revision_is_dataclass():
    from dataclasses import fields
    names = {f.name for f in fields(Revision)}
    assert names == {"rev_id", "cs_id", "date", "owner", "comment", "branch"}


# ── BlameLine ─────────────────────────────────────────────────────────────────

def test_blameline_fields():
    bl = BlameLine(line_no=3, owner="bob", cs_id=9, date=datetime(2026, 7, 24), content="pass")
    assert bl.line_no == 3
    assert bl.owner == "bob"
    assert bl.cs_id == 9
    assert bl.content == "pass"


def test_blameline_content_with_pipe():
    bl = BlameLine(line_no=1, owner="alice", cs_id=1, date=datetime(2026, 1, 1), content="x = a|b")
    assert bl.content == "x = a|b"


# ── Review ────────────────────────────────────────────────────────────────────

from biome_fm.plastic._models import Review, ChangelistInfo  # noqa: E402


def test_review_fields():
    from datetime import datetime
    r = Review(review_id=42, status="Reviewed", assignee="alice",
               date=datetime(2026, 1, 15), title="Fix memory leak")
    assert r.review_id == 42
    assert r.status == "Reviewed"
    assert r.assignee == "alice"
    assert r.title == "Fix memory leak"
    assert r.target_cs == 0


def test_review_is_frozen():
    from datetime import datetime
    r = Review(review_id=1, status="Under review", assignee="bob",
               date=datetime(2026, 1, 1), title="Test")
    try:
        r.review_id = 2  # type: ignore[misc]
        assert False, "should have raised"
    except (AttributeError, TypeError):
        pass


def test_review_equality():
    from datetime import datetime
    d = datetime(2026, 1, 1)
    r1 = Review(review_id=1, status="Reviewed", assignee="a", date=d, title="T")
    r2 = Review(review_id=1, status="Reviewed", assignee="a", date=d, title="T")
    assert r1 == r2


# ── ChangelistInfo ────────────────────────────────────────────────────────────

def test_changelist_info_fields():
    cl = ChangelistInfo(name="sprint-1", description="Sprint 1 work")
    assert cl.name == "sprint-1"
    assert cl.description == "Sprint 1 work"


def test_changelist_info_default_description():
    cl = ChangelistInfo(name="default")
    assert cl.description == ""


def test_changelist_info_is_frozen():
    cl = ChangelistInfo(name="test")
    try:
        cl.name = "other"  # type: ignore[misc]
        assert False, "should have raised"
    except (AttributeError, TypeError):
        pass
