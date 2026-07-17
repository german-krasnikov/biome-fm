"""Unit tests for FuzzyPresenter — no Qt required."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from biome_fm.presenters.fuzzy_presenter import FuzzyMatch, FuzzyPresenter


@pytest.fixture
def presenter():
    return FuzzyPresenter()


@pytest.fixture
def root(tmp_path):
    """Small file tree for scan tests."""
    (tmp_path / "readme.md").write_text("x")
    (tmp_path / "main.py").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "utils.py").write_text("x")
    return tmp_path


def test_score_exact_name_match_is_top(presenter, root):
    paths = [root / "readme.md", root / "main.py", root / "sub" / "utils.py"]
    matches = presenter.score("main", paths, root)
    assert matches[0].path == root / "main.py"


def test_score_empty_query_returns_all(presenter, root):
    paths = [root / "readme.md", root / "main.py"]
    matches = presenter.score("", paths, root)
    assert len(matches) == 2
    assert all(m.score == 1.0 for m in matches)


def test_score_returns_at_most_top_n(presenter, root):
    # Create more paths than TOP_N
    paths = [root / f"file{i}.txt" for i in range(FuzzyPresenter.TOP_N + 20)]
    matches = presenter.score("file", paths, root)
    assert len(matches) <= FuzzyPresenter.TOP_N


def test_score_filters_low_ratio(presenter, root):
    # "zzz" vs "readme.md" should score below 0.3
    paths = [root / "readme.md"]
    matches = presenter.score("zzzzzzzzz", paths, root)
    assert len(matches) == 0


def test_scan_respects_max_depth(tmp_path, presenter):
    # Create nesting deeper than MAX_DEPTH
    deep = tmp_path
    for i in range(FuzzyPresenter.MAX_DEPTH + 3):
        deep = deep / f"d{i}"
        deep.mkdir()
    (deep / "too_deep.txt").write_text("x")
    # A file at exactly MAX_DEPTH - 1 should be found; too_deep should not
    # Plant a file just inside the limit
    shallow = tmp_path
    for i in range(FuzzyPresenter.MAX_DEPTH - 1):
        shallow = shallow / f"d{i}"
    (shallow / "shallow.txt").write_text("x")

    done = threading.Event()
    result: list[list[Path]] = []

    def on_done(paths):
        result.append(paths)
        done.set()

    cancel = threading.Event()
    presenter.scan(tmp_path, cancel, on_done)
    done.wait(timeout=5)

    names = {p.name for p in result[0]}
    assert "shallow.txt" in names
    assert "too_deep.txt" not in names


def test_scan_cancel_stops_early(tmp_path, presenter):
    # Create a bunch of files
    for i in range(50):
        (tmp_path / f"file{i}.txt").write_text("x")

    done = threading.Event()
    result: list[list[Path]] = []

    cancel = threading.Event()
    cancel.set()  # cancel immediately

    def on_done(paths):
        result.append(paths)
        done.set()

    presenter.scan(tmp_path, cancel, on_done)
    done.wait(timeout=5)

    # on_done must be called even on cancel
    assert len(result) == 1
    # may be empty or partial — just check it's less than 50
    assert len(result[0]) < 50


def test_label_relative_to_root(presenter, root):
    p = root / "sub" / "utils.py"
    label = presenter._label(p, root)
    assert label == str(Path("sub") / "utils.py")
