"""TDD: F453 — ComparePanel view tests."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fi(name: str, size: int = 100) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=size, modified=0.0)


def _entry(name: str, status: CompareStatus, left: FileItem | None = None, right: FileItem | None = None) -> CompareEntry:
    return CompareEntry(name=name, status=status, left=left, right=right)


_LEFT_ONLY = _entry("a.txt", CompareStatus.LEFT_ONLY, left=_fi("a.txt", 10))
_EQUAL     = _entry("b.txt", CompareStatus.EQUAL,     left=_fi("b.txt", 20), right=_fi("b.txt", 20))
_RIGHT_ONLY = _entry("c.txt", CompareStatus.RIGHT_ONLY, right=_fi("c.txt", 30))
_NEWER_LEFT = _entry("d.txt", CompareStatus.NEWER_LEFT, left=_fi("d.txt", 40), right=_fi("d.txt", 40))


# ---------------------------------------------------------------------------
# CompareModel
# ---------------------------------------------------------------------------

class TestCompareModel:
    def test_row_count(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY, _EQUAL])
        assert m.rowCount() == 2

    def test_column_count(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY])
        assert m.columnCount() == 4

    def test_display_role_name(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY, _EQUAL])
        idx = m.index(0, 0)
        assert m.data(idx, Qt.ItemDataRole.DisplayRole) == "a.txt"

    def test_display_role_status(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY])
        idx = m.index(0, 1)
        assert m.data(idx, Qt.ItemDataRole.DisplayRole) == "left_only"

    def test_display_role_left_size(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY])
        idx = m.index(0, 2)
        assert m.data(idx, Qt.ItemDataRole.DisplayRole) == 10

    def test_display_role_right_size_missing(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY])
        idx = m.index(0, 3)
        assert m.data(idx, Qt.ItemDataRole.DisplayRole) == ""

    def test_foreground_left_only(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_LEFT_ONLY])
        idx = m.index(0, 1)
        color = m.data(idx, Qt.ItemDataRole.ForegroundRole)
        assert color == QColor("#e06c75")

    def test_foreground_equal_is_none(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_EQUAL])
        idx = m.index(0, 1)
        assert m.data(idx, Qt.ItemDataRole.ForegroundRole) is None

    def test_foreground_right_only(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_RIGHT_ONLY])
        idx = m.index(0, 1)
        assert m.data(idx, Qt.ItemDataRole.ForegroundRole) == QColor("#98c379")

    def test_foreground_newer_left(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([_NEWER_LEFT])
        idx = m.index(0, 1)
        assert m.data(idx, Qt.ItemDataRole.ForegroundRole) == QColor("#e5c07b")

    def test_invalid_index_returns_none(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([])
        assert m.data(m.index(99, 0), Qt.ItemDataRole.DisplayRole) is None

    def test_header_data(self) -> None:
        from biome_fm.views.compare_panel import CompareModel
        m = CompareModel([])
        assert m.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "Name"
        assert m.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "Status"


# ---------------------------------------------------------------------------
# ComparePanel
# ---------------------------------------------------------------------------

class TestComparePanel:
    def test_set_entries_updates_row_count(self, qtbot) -> None:
        from biome_fm.views.compare_panel import ComparePanel
        panel = ComparePanel()
        qtbot.addWidget(panel)
        panel.set_entries([_LEFT_ONLY, _EQUAL, _RIGHT_ONLY])
        assert panel._table.model().rowCount() == 3

    def test_status_label_updates(self, qtbot) -> None:
        from biome_fm.views.compare_panel import ComparePanel
        panel = ComparePanel()
        qtbot.addWidget(panel)
        panel.set_entries([_LEFT_ONLY, _EQUAL])
        text = panel._status_label.text()
        assert text  # non-empty

    def test_diff_requested_signal(self, qtbot) -> None:
        from biome_fm.views.compare_panel import ComparePanel
        panel = ComparePanel()
        qtbot.addWidget(panel)
        panel.set_entries([_LEFT_ONLY, _EQUAL])
        # Select first row
        panel._table.selectRow(0)
        with qtbot.waitSignal(panel.diff_requested, timeout=1000) as blocker:
            panel._act_diff.trigger()
        assert blocker.args[0] == _LEFT_ONLY

    def test_sync_left_to_right_signal(self, qtbot) -> None:
        from biome_fm.views.compare_panel import ComparePanel
        panel = ComparePanel()
        qtbot.addWidget(panel)
        panel.set_entries([_LEFT_ONLY, _EQUAL])
        panel._table.selectRow(0)
        with qtbot.waitSignal(panel.sync_left_to_right_requested, timeout=1000) as blocker:
            panel._act_sync_lr.trigger()
        assert _LEFT_ONLY in blocker.args[0]

    def test_sync_right_to_left_signal(self, qtbot) -> None:
        from biome_fm.views.compare_panel import ComparePanel
        panel = ComparePanel()
        qtbot.addWidget(panel)
        panel.set_entries([_RIGHT_ONLY])
        panel._table.selectRow(0)
        with qtbot.waitSignal(panel.sync_right_to_left_requested, timeout=1000) as blocker:
            panel._act_sync_rl.trigger()
        assert _RIGHT_ONLY in blocker.args[0]
