"""Unit tests for _reviews.py — parse + CLI wrappers (TDD RED phase)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from unittest.mock import call, patch

import pytest

from biome_fm.plastic._models import Review
from biome_fm.plastic._reviews import (
    REVIEW_STATUSES,
    create_review,
    delete_review,
    edit_review_status,
    parse_reviews,
)


# ── parse_reviews ─────────────────────────────────────────────────────────────

def test_parse_reviews_empty():
    assert parse_reviews("") == []


def test_parse_reviews_whitespace_only():
    assert parse_reviews("   \n\n  ") == []


def test_parse_reviews_basic():
    line = "42|Under review|alice|01/15/2026 10:30:00|Fix memory leak"
    r = parse_reviews(line)[0]
    assert r.review_id == 42
    assert r.status == "Under review"
    assert r.assignee == "alice"
    assert r.date == datetime(2026, 1, 15, 10, 30, 0)
    assert r.title == "Fix memory leak"


def test_parse_reviews_title_with_pipe():
    """title is the last field, split with maxsplit=4 so pipes in title are preserved."""
    line = "1|Reviewed|bob|01/01/2026 00:00:00|Title with | pipe"
    r = parse_reviews(line)[0]
    assert r.title == "Title with | pipe"


def test_parse_reviews_multiple_lines():
    output = (
        "1|Reviewed|bob|01/01/2026 00:00:00|First\n"
        "2|Under review|alice|02/01/2026 00:00:00|Second\n"
    )
    reviews = parse_reviews(output)
    assert len(reviews) == 2
    assert reviews[0].review_id == 1
    assert reviews[1].review_id == 2


def test_parse_reviews_malformed_lines_skipped():
    """Lines that can't be parsed are silently skipped."""
    output = (
        "bad line without enough fields\n"
        "42|Reviewed|alice|01/01/2026 00:00:00|Good\n"
        "also bad\n"
    )
    reviews = parse_reviews(output)
    assert len(reviews) == 1
    assert reviews[0].review_id == 42


def test_parse_reviews_non_integer_id_skipped():
    line = "notanint|Reviewed|alice|01/01/2026 00:00:00|Title"
    assert parse_reviews(line) == []


# ── REVIEW_STATUSES constant ──────────────────────────────────────────────────

def test_review_statuses_has_three():
    assert len(REVIEW_STATUSES) == 3
    assert "Under review" in REVIEW_STATUSES
    assert "Reviewed" in REVIEW_STATUSES
    assert "Rework required" in REVIEW_STATUSES


# ── CLI wrappers ──────────────────────────────────────────────────────────────

def test_create_review_basic(tmp_path):
    with patch("biome_fm.plastic._reviews.run_cm") as mock:
        create_review(100, "My Review", tmp_path)
    mock.assert_called_once_with(
        ["codereview", "cs:100", "My Review", '--status=Under review'],
        cwd=tmp_path,
    )


def test_create_review_with_assignee(tmp_path):
    with patch("biome_fm.plastic._reviews.run_cm") as mock:
        create_review(100, "My Review", tmp_path, assignee="alice")
    args = mock.call_args[0][0]
    assert "--assignee=alice" in args


def test_create_review_with_status(tmp_path):
    with patch("biome_fm.plastic._reviews.run_cm") as mock:
        create_review(100, "Review", tmp_path, status="Reviewed")
    args = mock.call_args[0][0]
    assert "--status=Reviewed" in args


def test_edit_review_status(tmp_path):
    with patch("biome_fm.plastic._reviews.run_cm") as mock:
        edit_review_status(42, "Reviewed", tmp_path)
    mock.assert_called_once_with(
        ["codereview", "-e", "42", "--status=Reviewed"],
        cwd=tmp_path,
    )


def test_delete_review(tmp_path):
    with patch("biome_fm.plastic._reviews.run_cm") as mock:
        delete_review(7, tmp_path)
    mock.assert_called_once_with(
        ["codereview", "-d", "7"],
        cwd=tmp_path,
    )


# ── Presenter integration (via FakeView) ──────────────────────────────────────

@dataclass
class _FakeView:
    reviews: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    busy: list = field(default_factory=list)
    status_items: list = field(default_factory=list)
    changesets: list = field(default_factory=list)
    branches: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    shelves: list = field(default_factory=list)
    changelist_status: dict = field(default_factory=dict)
    header: object = None
    diffs: list = field(default_factory=list)

    def set_reviews(self, items):           self.reviews = list(items)
    def show_error(self, m):                self.errors.append(m)
    def set_busy(self, b):                  self.busy.append(b)
    def set_status_items(self, i):          self.status_items = list(i)
    def set_changesets(self, i):            self.changesets = list(i)
    def set_branches(self, i):             self.branches = list(i)
    def set_labels(self, i):               self.labels = list(i)
    def set_shelves(self, i):              self.shelves = list(i)
    def set_changelist_status(self, g):    self.changelist_status = dict(g)
    def set_header(self, b, r):            self.header = (b, r)
    def set_status_message(self, m):       pass
    def show_diff(self, t):                self.diffs.append(t)
    def show_history(self, p, i):          pass
    def show_blame(self, p, i):            pass
    def set_workspace_info(self, wi):      pass
    def show_find_results(self, ps):       pass
    def set_xlinks(self, items):           pass
    def show_attributes(self, s, i):       pass
    def show_acl(self, s, i):              pass
    def set_users(self, i):                pass
    def set_groups(self, i):               pass
    def set_dag(self, n, b):               pass
    def show_merge_sides(self, p, b, s, d): pass


_REVIEW_LINE = "1|Reviewed|bob|01/01/2026 00:00:00|Title"


@pytest.fixture
def fake_view():
    return _FakeView()


@pytest.fixture
def cwd(tmp_path):
    return tmp_path


def _make_presenter(view, cwd):
    from biome_fm.plastic._presenter import PlasticPresenter
    return PlasticPresenter(view=view, cwd=cwd)


def test_load_reviews_drains_to_view(fake_view, cwd):
    def _dispatch(args, cwd=None, safe=False, timeout=10):
        if args[0] == "find" and "reviews" in args:
            return _REVIEW_LINE
        return ""

    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_dispatch):
        p = _make_presenter(fake_view, cwd)
        p.load_reviews()
        p.drain()

    assert len(fake_view.reviews) == 1
    assert fake_view.reviews[0].review_id == 1


def test_create_review_calls_cm_and_reloads(fake_view, cwd):
    with patch("biome_fm.plastic._presenter._create_review") as mock_cr, \
         patch("biome_fm.plastic._presenter.run_cm", return_value=_REVIEW_LINE):
        p = _make_presenter(fake_view, cwd)
        p.create_review(100, "My Review", assignee="alice")
        p.drain()

    mock_cr.assert_called_once_with(100, "My Review", cwd, assignee="alice", status="Under review")
    assert len(fake_view.reviews) == 1


def test_delete_review_calls_cm_and_reloads(fake_view, cwd):
    with patch("biome_fm.plastic._presenter._delete_review") as mock_dr, \
         patch("biome_fm.plastic._presenter.run_cm", return_value=""):
        p = _make_presenter(fake_view, cwd)
        p.delete_review(42)
        p.drain()

    mock_dr.assert_called_once_with(42, cwd)


def test_edit_review_status_calls_cm(fake_view, cwd):
    with patch("biome_fm.plastic._presenter._edit_review_status") as mock_er, \
         patch("biome_fm.plastic._presenter.run_cm", return_value=""):
        p = _make_presenter(fake_view, cwd)
        p.edit_review_status(7, "Reviewed")
        p.drain()

    mock_er.assert_called_once_with(7, "Reviewed", cwd)
