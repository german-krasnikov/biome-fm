"""Unit tests for back/forward history stack properties on PanePresenter."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter

A = Path("/a")
B = Path("/b")
C = Path("/c")

TREE = {A: [], B: [], C: []}


class FakeVFS:
    def listdir(self, p: Path) -> list[FileItem]:
        if p not in TREE:
            raise FileNotFoundError(p)
        return []


@dataclass
class FakeView:
    items: list = field(default_factory=list)
    path: Path | None = None
    errors: list = field(default_factory=list)
    status: str = ""
    marked: set = field(default_factory=set)
    cursor: FileItem | None = None
    nav_history: list = field(default_factory=list)
    selected: str | None = None
    back_paths: list = field(default_factory=list)
    fwd_paths: list = field(default_factory=list)

    def set_items(self, items, **kw): self.items = list(items)
    def set_path(self, p): self.path = p
    def show_error(self, m): self.errors.append(m)
    def set_status(self, t): self.status = t
    def set_marked(self, m): self.marked = m
    def current_cursor_item(self): return self.cursor
    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v): pass
    def set_nav_history(self, h): self.nav_history = h
    def select_item(self, n): self.selected = n
    def set_dir_size(self, p, s): pass
    def set_back_history(self, paths): self.back_paths = paths
    def set_forward_history(self, paths): self.fwd_paths = paths


@pytest.fixture
def presenter():
    return PanePresenter(FakeView(), FakeVFS())


def test_back_stack_empty_initially(presenter) -> None:
    assert presenter.back_stack == []


def test_back_stack_property(presenter) -> None:
    presenter.navigate_to(A)
    presenter.navigate_to(B)
    presenter.navigate_to(C)
    # After A→B→C: back_stack = [B, A] (most recent first)
    assert presenter.back_stack == [B, A]


def test_forward_stack_property(presenter) -> None:
    presenter.navigate_to(A)
    presenter.navigate_to(B)
    presenter.go_back()
    # After going back: forward_stack = [B]
    assert presenter.forward_stack == [B]
