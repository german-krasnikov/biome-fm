"""F310 — Screen Reader Accessible Names (RED phase)."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_pane_view_widgets_have_names(qtbot) -> None:
    from biome_fm.views.pane_view import PaneView

    v = PaneView()
    qtbot.addWidget(v)
    assert v._table.accessibleName() == "File list"
    assert v._btn_back.accessibleName() == "Back"
    assert v._btn_fwd.accessibleName() == "Forward"
    assert v._btn_new_tab.accessibleName() == "New tab"
    assert v._status_label.accessibleName() == "Status"
    assert v.filter_bar.accessibleName() == "Filter"


def test_main_window_widgets_have_names(qtbot) -> None:
    from biome_fm.views.main_window import MainWindow

    w = MainWindow()
    qtbot.addWidget(w)
    assert w._cmd_line.accessibleName() == "Command line"
    assert w.action_bar.accessibleName() == "Action bar"
