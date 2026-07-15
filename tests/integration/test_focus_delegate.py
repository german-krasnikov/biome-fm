"""Integration test: focus rect suppression in _DropHintDelegate."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem

from biome_fm.views.pane_view import _DropHintDelegate, _PaneTableView


def test_init_style_option_strips_focus_and_selection(qtbot):
    table = _PaneTableView()
    qtbot.addWidget(table)
    delegate = _DropHintDelegate(table)
    opt = QStyleOptionViewItem()
    opt.state = QStyle.StateFlag.State_HasFocus | QStyle.StateFlag.State_Selected
    delegate.initStyleOption(opt, QModelIndex())
    assert not (opt.state & QStyle.StateFlag.State_HasFocus)
    assert not (opt.state & QStyle.StateFlag.State_Selected)
