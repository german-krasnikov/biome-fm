"""Tests for SearchScope — TDD, no Qt."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter, SearchScope


def _item(path: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=is_dir, size=0, modified=0.0)


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """
    root/
      root_file.txt
      sub/
        nested.txt
    """
    (tmp_path / "root_file.txt").write_text("root")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested")
    return tmp_path


# ── existing scope tests (unchanged) ────────────────────────────────────────

def test_subtree_finds_nested(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(
        "*.txt", scope=SearchScope.SUBTREE
    )
    names = {r.item.name for r in results}
    assert "nested.txt" in names


def test_current_dir_skips_subdirs(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(
        "*.txt", scope=SearchScope.CURRENT_DIR
    )
    names = {r.item.name for r in results}
    assert "root_file.txt" in names
    assert "nested.txt" not in names


# ── new enum values ──────────────────────────────────────────────────────────

def test_selected_files_in_enum() -> None:
    assert SearchScope.SELECTED_FILES.value == "selected"


def test_both_panes_in_enum() -> None:
    assert SearchScope.BOTH_PANES.value == "both_panes"


# ── SearchPresenter.match_item ───────────────────────────────────────────────

def test_match_item_wildcard_match(tmp_path: Path) -> None:
    p = tmp_path / "foo.py"
    p.write_text("")
    presenter = SearchPresenter(LocalVFS(), tmp_path)
    result = presenter.match_item(_item(p), "*.py", SearchMode.NAME_WILDCARD)
    assert result is not None
    assert result.item.name == "foo.py"


def test_match_item_wildcard_no_match(tmp_path: Path) -> None:
    p = tmp_path / "foo.txt"
    p.write_text("")
    presenter = SearchPresenter(LocalVFS(), tmp_path)
    assert presenter.match_item(_item(p), "*.py", SearchMode.NAME_WILDCARD) is None


def test_match_item_content(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("hello world")
    presenter = SearchPresenter(LocalVFS(), tmp_path)
    assert presenter.match_item(_item(p), "hello", SearchMode.CONTENT) is not None


# ── coordinator: SELECTED_FILES scope ────────────────────────────────────────

class _Panel:
    def __init__(self) -> None:
        self.results: list = []
        self.finished: int | None = None
        self.cancelled = False
        self.result_count = 0

    def on_search_started(self, q: str) -> None: ...
    def add_results(self, batch: list) -> None:
        self.results.extend(batch)
        self.result_count = len(self.results)
    def on_finished(self, n: int) -> None: self.finished = n
    def on_cancelled(self) -> None: self.cancelled = True


def _drain_until_done(sc, panel: _Panel, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while panel.finished is None and not panel.cancelled and time.monotonic() < deadline:
        sc.drain()
        time.sleep(0.01)


def test_selected_scope_searches_marked_files_only(tmp_path: Path) -> None:
    from unittest.mock import patch
    from biome_fm.presenters.search_coordinator import SearchCoordinator

    vfs = LocalVFS()
    a = tmp_path / "a.py"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.py"
    for f in (a, b, c):
        f.write_text("")

    # Only a and b are marked; c is not
    marked = [_item(a), _item(b)]

    active = MagicMock()
    active.current_path = tmp_path
    active.marked_items = marked

    manager = MagicMock()
    manager.active_pane_id = "left"

    panel = _Panel()
    sc = SearchCoordinator(
        vfs=vfs,
        coord=MagicMock(toggle=lambda *a: None),
        manager=manager,
        panel=panel,
        get_active=lambda: active,
    )

    fake_params = (
        "*.py", SearchMode.NAME_WILDCARD, 100,
        SearchScope.SELECTED_FILES, None, [], False, False, 0,
    )
    with patch("biome_fm.views.search_dialog.SearchDialog.get_params", return_value=fake_params):
        sc.request_search()

    _drain_until_done(sc, panel)

    assert panel.finished is not None, "search did not complete"
    names = {r.item.name for r in panel.results}
    assert "a.py" in names          # marked, matches *.py
    assert "b.txt" not in names     # marked but doesn't match *.py
    assert "c.py" not in names      # matches *.py but NOT marked


def test_both_panes_searches_both_roots(tmp_path: Path) -> None:
    from unittest.mock import patch
    from biome_fm.presenters.search_coordinator import SearchCoordinator

    vfs = LocalVFS()
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    (left_root / "left_file.txt").write_text("")
    (right_root / "right_file.txt").write_text("")

    active = MagicMock()
    active.current_path = left_root

    inactive_pane = MagicMock()
    inactive_pane.current_path = right_root

    manager = MagicMock()
    manager.active_pane_id = "left"
    manager.inactive_pane = inactive_pane

    panel = _Panel()
    sc = SearchCoordinator(
        vfs=vfs,
        coord=MagicMock(toggle=lambda *a: None),
        manager=manager,
        panel=panel,
        get_active=lambda: active,
    )

    fake_params = (
        "*.txt", SearchMode.NAME_WILDCARD, 100,
        SearchScope.BOTH_PANES, None, [], False, False, 0,
    )
    with patch("biome_fm.views.search_dialog.SearchDialog.get_params", return_value=fake_params):
        sc.request_search()

    _drain_until_done(sc, panel)

    assert panel.finished is not None, "search did not complete"
    names = {r.item.name for r in panel.results}
    assert "left_file.txt" in names
    assert "right_file.txt" in names


def test_both_panes_deduplicates_same_root(tmp_path: Path) -> None:
    """If both panes are in the same dir, search it only once."""
    from unittest.mock import patch
    from biome_fm.presenters.search_coordinator import SearchCoordinator

    vfs = LocalVFS()
    (tmp_path / "file.txt").write_text("")

    active = MagicMock()
    active.current_path = tmp_path

    inactive_pane = MagicMock()
    inactive_pane.current_path = tmp_path  # same dir

    manager = MagicMock()
    manager.active_pane_id = "left"
    manager.inactive_pane = inactive_pane

    panel = _Panel()
    sc = SearchCoordinator(
        vfs=vfs,
        coord=MagicMock(toggle=lambda *a: None),
        manager=manager,
        panel=panel,
        get_active=lambda: active,
    )

    fake_params = (
        "*.txt", SearchMode.NAME_WILDCARD, 100,
        SearchScope.BOTH_PANES, None, [], False, False, 0,
    )
    with patch("biome_fm.views.search_dialog.SearchDialog.get_params", return_value=fake_params):
        sc.request_search()

    _drain_until_done(sc, panel)

    # file.txt should appear exactly once
    assert panel.results.count(panel.results[0]) == 1
    assert len([r for r in panel.results if r.item.name == "file.txt"]) == 1
