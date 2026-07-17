"""Integration test: focus rect suppression in _DropHintDelegate."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView, _DropHintDelegate, _PaneTableView


def test_init_style_option_strips_focus_and_selection(qtbot):
    table = _PaneTableView()
    qtbot.addWidget(table)
    delegate = _DropHintDelegate(table)
    opt = QStyleOptionViewItem()
    opt.state = QStyle.StateFlag.State_HasFocus | QStyle.StateFlag.State_Selected
    delegate.initStyleOption(opt, QModelIndex())
    assert not (opt.state & QStyle.StateFlag.State_HasFocus)
    assert not (opt.state & QStyle.StateFlag.State_Selected)


def test_cursor_row_updates_on_selection_change(qtbot):
    """I15: _cursor_row cache matches the selected row without currentIndex() call."""
    view = PaneView()
    qtbot.addWidget(view)
    items = [
        FileItem(name=f"file{i}.txt", path=Path(f"/tmp/file{i}.txt"),
                 is_dir=False, size=0, modified=0.0)
        for i in range(5)
    ]
    view.set_items(items)
    view._table.selectRow(2)
    qtbot.wait(10)
    assert view._table._cursor_row == 2
