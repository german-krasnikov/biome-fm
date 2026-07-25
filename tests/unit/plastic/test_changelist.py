"""Unit tests for _changelist.py — parse + CLI wrappers (TDD RED phase)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._changelist import (
    add_to_changelist,
    create_changelist,
    delete_changelist,
    parse_changelist_status,
    remove_from_changelist,
)
from biome_fm.plastic._models import PlasticItem


# ── parse_changelist_status ───────────────────────────────────────────────────

def test_parse_changelist_status_empty(tmp_path):
    assert parse_changelist_status("", tmp_path) == {}


def test_parse_changelist_status_whitespace_only(tmp_path):
    assert parse_changelist_status("  \n  ", tmp_path) == {}


def test_parse_changelist_status_basic(tmp_path):
    output = (
        "Changelist 'feature':\n"
        "  CO|/repo/src/a.py\n"
        "  AD|/repo/src/b.py\n"
    )
    result = parse_changelist_status(output, Path("/repo"))
    assert "feature" in result
    assert len(result["feature"]) == 2
    assert result["feature"][0].status == "CO"
    assert result["feature"][1].status == "AD"


def test_parse_changelist_status_multiple_changelists(tmp_path):
    output = (
        "Changelist 'sprint-1':\n"
        "  CO|/repo/src/a.py\n"
        "Changelist 'sprint-2':\n"
        "  AD|/repo/src/b.py\n"
    )
    result = parse_changelist_status(output, Path("/repo"))
    assert "sprint-1" in result
    assert "sprint-2" in result
    assert len(result["sprint-1"]) == 1
    assert len(result["sprint-2"]) == 1


def test_parse_changelist_status_unknown_codes_skipped(tmp_path):
    output = (
        "Changelist 'test':\n"
        "  CO|/repo/src/a.py\n"
        "  XX|/repo/src/bad.py\n"
    )
    result = parse_changelist_status(output, Path("/repo"))
    assert len(result["test"]) == 1
    assert result["test"][0].status == "CO"


def test_parse_changelist_status_relative_paths_resolved(tmp_path):
    output = (
        "Changelist 'cl':\n"
        "  CO|src/a.py\n"
    )
    result = parse_changelist_status(output, tmp_path)
    # Relative paths should be resolved to absolute
    assert result["cl"][0].path.is_absolute()


# ── CLI wrappers ──────────────────────────────────────────────────────────────

def test_create_changelist_no_description(tmp_path):
    with patch("biome_fm.plastic._changelist.run_cm") as mock:
        create_changelist("sprint-1", tmp_path)
    mock.assert_called_once_with(["changelist", "create", "sprint-1"], cwd=tmp_path)


def test_create_changelist_with_description(tmp_path):
    with patch("biome_fm.plastic._changelist.run_cm") as mock:
        create_changelist("sprint-1", tmp_path, "Sprint 1 work")
    mock.assert_called_once_with(
        ["changelist", "create", "sprint-1", "Sprint 1 work"], cwd=tmp_path
    )


def test_delete_changelist(tmp_path):
    with patch("biome_fm.plastic._changelist.run_cm") as mock:
        delete_changelist("sprint-1", tmp_path)
    mock.assert_called_once_with(["changelist", "delete", "sprint-1"], cwd=tmp_path)


def test_add_to_changelist(tmp_path):
    paths = [Path("/repo/src/a.py"), Path("/repo/src/b.py")]
    with patch("biome_fm.plastic._changelist.run_cm") as mock:
        add_to_changelist("sprint-1", paths, tmp_path)
    args = mock.call_args[0][0]
    assert args[0] == "changelist"
    assert args[1] == "sprint-1"
    assert "add" in args
    assert "/repo/src/a.py" in args
    assert "/repo/src/b.py" in args


def test_remove_from_changelist(tmp_path):
    paths = [Path("/repo/src/a.py")]
    with patch("biome_fm.plastic._changelist.run_cm") as mock:
        remove_from_changelist("sprint-1", paths, tmp_path)
    args = mock.call_args[0][0]
    assert "rm" in args
    assert "/repo/src/a.py" in args


# ── Presenter integration ──────────────────────────────────────────────────────

@dataclass
class _FakeView:
    changelist_status: dict = field(default_factory=dict)
    reviews: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    busy: list = field(default_factory=list)
    status_items: list = field(default_factory=list)
    changesets: list = field(default_factory=list)
    branches: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    shelves: list = field(default_factory=list)
    header: object = None
    diffs: list = field(default_factory=list)

    def set_changelist_status(self, g): self.changelist_status = dict(g)
    def set_reviews(self, i):           self.reviews = list(i)
    def show_error(self, m):            self.errors.append(m)
    def set_busy(self, b):              self.busy.append(b)
    def set_status_items(self, i):      self.status_items = list(i)
    def set_changesets(self, i):        self.changesets = list(i)
    def set_branches(self, i):         self.branches = list(i)
    def set_labels(self, i):           self.labels = list(i)
    def set_shelves(self, i):          self.shelves = list(i)
    def set_header(self, b, r):        self.header = (b, r)
    def set_status_message(self, m):   pass
    def show_diff(self, t):            self.diffs.append(t)
    def show_history(self, p, i):      pass
    def show_blame(self, p, i):        pass
    def set_workspace_info(self, wi):  pass
    def show_find_results(self, ps):   pass
    def set_xlinks(self, items):       pass
    def show_attributes(self, s, i):   pass
    def show_acl(self, s, i):          pass
    def set_users(self, i):            pass
    def set_groups(self, i):           pass
    def set_dag(self, n, b):           pass
    def show_merge_sides(self, p, b, s, d): pass


_CL_OUTPUT = "Changelist 'sprint-1':\n  CO|/repo/src/a.py\n"


@pytest.fixture
def fake_view():
    return _FakeView()


@pytest.fixture
def cwd(tmp_path):
    return tmp_path


def _make_presenter(view, cwd):
    from biome_fm.plastic._presenter import PlasticPresenter
    return PlasticPresenter(view=view, cwd=cwd)


def test_load_changelist_status_drains_to_view(fake_view, cwd):
    def _dispatch(args, cwd=None, safe=False, timeout=10):
        if args[0] == "status" and "--changelists" in args:
            return _CL_OUTPUT
        return ""

    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_dispatch):
        p = _make_presenter(fake_view, cwd)
        p.load_changelist_status()
        p.drain()

    assert "sprint-1" in fake_view.changelist_status


def test_move_to_changelist_calls_add(fake_view, cwd):
    item = PlasticItem(status="CO", path=Path("/repo/src/foo.py"))

    with patch("biome_fm.plastic._presenter.add_to_changelist") as mock_add, \
         patch("biome_fm.plastic._presenter.run_cm", return_value=""):
        p = _make_presenter(fake_view, cwd)
        p.move_to_changelist([item], "sprint-1")
        p.drain()

    mock_add.assert_called_once_with("sprint-1", [item.path], cwd)


def test_delete_changelist_calls_cm(fake_view, cwd):
    with patch("biome_fm.plastic._presenter._delete_changelist") as mock_dc, \
         patch("biome_fm.plastic._presenter.run_cm", return_value=""):
        p = _make_presenter(fake_view, cwd)
        p.delete_changelist("sprint-1")
        p.drain()

    mock_dc.assert_called_once_with("sprint-1", cwd)
