"""Integration tests for SyncDialog."""
import os
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.views.sync_dialog import SyncDialog

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

LEFT_ROOT = Path("/left")
RIGHT_ROOT = Path("/right")


def _entry(name: str, status: CompareStatus, left=None, right=None) -> CompareEntry:
    return CompareEntry(name=name, status=status, left=left, right=right)


def _item(name: str, root: Path) -> FileItem:
    return FileItem(name=name, path=root / name, is_dir=False, size=512, modified=1.0)


@pytest.fixture
def entries():
    return [
        _entry("a.txt", CompareStatus.LEFT_ONLY, left=_item("a.txt", LEFT_ROOT)),
        _entry("b.txt", CompareStatus.RIGHT_ONLY, right=_item("b.txt", RIGHT_ROOT)),
        _entry("c.txt", CompareStatus.EQUAL,
               left=_item("c.txt", LEFT_ROOT), right=_item("c.txt", RIGHT_ROOT)),
    ]


def test_dialog_shows_entries(qtbot, entries):
    dlg = SyncDialog(entries, LEFT_ROOT, RIGHT_ROOT)
    qtbot.addWidget(dlg)
    assert dlg._table.rowCount() == 3


def test_sync_button_emits(qtbot, entries):
    dlg = SyncDialog(entries, LEFT_ROOT, RIGHT_ROOT)
    qtbot.addWidget(dlg)
    with qtbot.waitSignal(dlg.sync_requested, timeout=1000) as blocker:
        dlg._btn_ltr.click()
    checked_entries, direction = blocker.args
    assert direction == "left_to_right"
    # only non-EQUAL rows are pre-checked
    assert all(e.status != CompareStatus.EQUAL for e in checked_entries)
