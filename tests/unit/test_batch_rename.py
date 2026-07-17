"""Unit tests for ManagerPresenter.multi_rename (TDD — red phase)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.presenters.manager_presenter import ManagerPresenter


class _FakeVFS:
    def __init__(self) -> None:
        self.moves: list[tuple[Path, Path]] = []

    def listdir(self, path: Path) -> list:
        return []

    def move(self, src: Path, dst: Path) -> None:
        self.moves.append((src, dst))


class _FakePane:
    current_path = Path("/tmp")

    def refresh(self) -> None:
        pass

    def navigate_to(self, path: Path) -> None:
        pass


def _mgr(vfs: _FakeVFS) -> ManagerPresenter:
    return ManagerPresenter(_FakePane(), _FakePane(), vfs)


def test_multi_rename_calls_vfs(tmp_path: Path) -> None:
    vfs = _FakeVFS()
    a = tmp_path / "a.txt"
    a.touch()
    _mgr(vfs).multi_rename([(a, "b.txt")])
    assert vfs.moves == [(a, tmp_path / "b.txt")]


def test_multi_rename_empty_is_noop() -> None:
    vfs = _FakeVFS()
    _mgr(vfs).multi_rename([])
    assert vfs.moves == []


def test_multi_rename_undo(tmp_path: Path) -> None:
    vfs = _FakeVFS()
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.touch()
    mgr = _mgr(vfs)
    mgr.multi_rename([(a, "b.txt")])
    mgr.undo()
    assert vfs.moves == [(a, b), (b, a)]
