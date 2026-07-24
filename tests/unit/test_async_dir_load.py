"""Unit tests for chunked async dir loading (Item #59). No Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


@dataclass
class FakeView:
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    errors: list[str] = field(default_factory=list)
    status: str = ""
    marked: set[Path] = field(default_factory=set)
    nav_history: list[Path] = field(default_factory=list)
    selected: str | None = None

    def set_items(self, items: list[FileItem], **_: object) -> None:
        self.items = list(items)

    def set_path(self, p: Path) -> None:
        self.path = p

    def show_error(self, msg: str) -> None:
        self.errors.append(msg)

    def set_status(self, text: str) -> None:
        self.status = text

    def set_marked(self, paths: set[Path]) -> None:
        self.marked = set(paths)

    def current_cursor_item(self) -> FileItem | None:
        return None

    def advance_cursor(self) -> None: pass
    def retreat_cursor(self) -> None: pass
    def set_filter_visible(self, visible: bool) -> None: pass

    def set_nav_history(self, paths: list[Path]) -> None:
        self.nav_history = list(paths)

    def select_item(self, name: str) -> None:
        self.selected = name

    def set_dir_size(self, path: Path, size: int) -> None: pass


@pytest.fixture
def view() -> FakeView:
    return FakeView()


@pytest.fixture
def presenter(view: FakeView):
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter
    return PanePresenter(view=view, vfs=LocalVFS())


def test_navigate_shows_loading_status(presenter, view, tmp_path):
    """set_path and 'Loading...' are immediate — before drain."""
    presenter.navigate_to(tmp_path)
    assert view.path == tmp_path
    assert "Loading" in view.status


def test_navigate_items_empty_before_drain(presenter, view, tmp_path):
    """Items not delivered until drain_nav() is called."""
    (tmp_path / "a.txt").touch()
    presenter.navigate_to(tmp_path)
    assert view.items == []  # not yet


def test_navigate_drain_delivers_items(presenter, view, tmp_path):
    """After drain_nav(), items from listdir appear in view."""
    (tmp_path / "a.txt").touch()
    presenter.navigate_to(tmp_path)
    presenter._nav_future.result()  # wait for pool job
    presenter.drain_nav()
    assert any(i.name == "a.txt" for i in view.items)


def test_stale_result_discarded(presenter, view, tmp_path):
    """A result queued for a previous path is silently discarded."""
    dir_a = tmp_path / "a"
    dir_a.mkdir()
    dir_b = tmp_path / "b"
    dir_b.mkdir()
    presenter.navigate_to(dir_a)
    presenter.navigate_to(dir_b)  # _nav_pending = dir_b now
    # manually inject a stale dir_a result
    presenter._nav_queue.put((dir_a, [], None, False))
    presenter.drain_nav()  # must discard dir_a result
    assert presenter._cwd != dir_a


def test_oserror_shows_error(presenter, view):
    """OSError from listdir surfaces via show_error; _cwd stays None."""
    presenter.navigate_to(Path("/nonexistent/__xyz_9182736__"))
    presenter._nav_future.result()
    presenter.drain_nav()
    assert view.errors
    assert presenter._cwd is None
