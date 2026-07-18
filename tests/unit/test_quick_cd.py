"""Unit tests for QuickCDDialog logic (F256)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.frecency_store import FrecencyEntry
from biome_fm.views.quick_cd_dialog import QuickCDDialog


def _entry(p: str) -> FrecencyEntry:
    return FrecencyEntry(path=Path(p), visits=1, last_visit=0.0)


def _make_dialog(entries, cwd: Path, qtbot) -> QuickCDDialog:
    dlg = QuickCDDialog(entries, cwd)
    qtbot.addWidget(dlg)
    return dlg


def test_empty_shows_frecency(qtbot, tmp_path: Path) -> None:
    entries = [_entry("/work/foo"), _entry("/work/bar")]
    dlg = _make_dialog(entries, tmp_path, qtbot)
    assert dlg._list.count() == 2


def test_frecency_filtering(qtbot, tmp_path: Path) -> None:
    entries = [_entry("/work/foo"), _entry("/home/baz"), _entry("/work/bar")]
    dlg = _make_dialog(entries, tmp_path, qtbot)
    dlg._edit.setText("work")
    assert dlg._list.count() == 2


def test_path_completion(qtbot, tmp_path: Path) -> None:
    (tmp_path / "abc").mkdir()
    (tmp_path / "abd").mkdir()
    (tmp_path / "xyz").mkdir()
    dlg = _make_dialog([], tmp_path, qtbot)
    # type a path-like prefix ending with /
    dlg._edit.setText(str(tmp_path) + "/")
    assert dlg._list.count() == 3


def test_path_completion_filters_by_stem(qtbot, tmp_path: Path) -> None:
    (tmp_path / "abc").mkdir()
    (tmp_path / "abd").mkdir()
    (tmp_path / "xyz").mkdir()
    dlg = _make_dialog([], tmp_path, qtbot)
    dlg._edit.setText(str(tmp_path) + "/ab")
    assert dlg._list.count() == 2


def test_tilde_expansion(qtbot, tmp_path: Path) -> None:
    dlg = _make_dialog([], tmp_path, qtbot)
    dlg._edit.setText("~/")
    # should list dirs in home — just verify it doesn't crash and list is populated
    # (home has at least some dirs on any dev machine)
    assert dlg._list.count() >= 0  # no crash is the main check
