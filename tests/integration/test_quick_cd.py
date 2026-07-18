"""Integration tests for QuickCDDialog (F256)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.frecency_store import FrecencyEntry
from biome_fm.views.quick_cd_dialog import QuickCDDialog


def _entry(p: str) -> FrecencyEntry:
    return FrecencyEntry(path=Path(p), visits=1, last_visit=0.0)


def test_dialog_opens(qtbot, tmp_path: Path) -> None:
    entries = [_entry(str(tmp_path))]
    dlg = QuickCDDialog(entries, tmp_path)
    qtbot.addWidget(dlg)
    assert dlg._list.count() >= 1


def test_path_selected_signal(qtbot, tmp_path: Path) -> None:
    sub = tmp_path / "subdir"
    sub.mkdir()
    dlg = QuickCDDialog([], tmp_path)
    qtbot.addWidget(dlg)
    received: list[Path] = []
    dlg.path_selected.connect(received.append)
    dlg._edit.setText(str(tmp_path) + "/")
    assert dlg._list.count() >= 1
    # activate first item
    dlg._list.setCurrentRow(0)
    dlg._on_return()
    assert len(received) == 1
    assert received[0].is_dir()
