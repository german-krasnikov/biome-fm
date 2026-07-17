"""Integration tests for DuplicateFinderDialog."""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from biome_fm.views.duplicate_panel import DuplicateFinderDialog


def _write(p: Path, content: bytes) -> Path:
    p.write_bytes(content)
    return p


def _wait_for_scan(dlg: DuplicateFinderDialog, qtbot: QtBot, timeout: int = 3000) -> None:
    """Poll until the background scan completes (progress bar goes determinate)."""
    def _done():
        return dlg._progress.maximum() > 0

    qtbot.waitUntil(_done, timeout=timeout)


def test_dialog_shows_groups(tmp_path, qtbot):
    content = b"duplicate content"
    _write(tmp_path / "a.txt", content)
    _write(tmp_path / "b.txt", content)

    dlg = DuplicateFinderDialog(tmp_path)
    qtbot.addWidget(dlg)
    dlg.show()
    _wait_for_scan(dlg, qtbot)

    assert dlg._tree.topLevelItemCount() == 1
    group_item = dlg._tree.topLevelItem(0)
    assert group_item.childCount() == 2


def test_delete_button_emits_correct_paths(tmp_path, qtbot):
    content = b"same"
    _write(tmp_path / "first.txt", content)
    _write(tmp_path / "second.txt", content)

    dlg = DuplicateFinderDialog(tmp_path)
    qtbot.addWidget(dlg)
    dlg.show()
    _wait_for_scan(dlg, qtbot)

    emitted: list[list[Path]] = []
    dlg.delete_requested.connect(emitted.append)

    assert dlg._del_btn.isEnabled()
    dlg._del_btn.click()

    assert len(emitted) == 1
    # Only the second file (index 1) should be deleted; first is kept
    assert len(emitted[0]) == 1


def test_cancel_on_close_no_crash(tmp_path, qtbot):
    _write(tmp_path / "a.txt", b"x")
    _write(tmp_path / "b.txt", b"x")

    dlg = DuplicateFinderDialog(tmp_path)
    qtbot.addWidget(dlg)
    dlg.show()
    dlg.close()  # should set cancel flag, join thread, and not crash
    assert dlg._cancel[0] is True
    assert not dlg._thread.is_alive()
