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


# ── Item #49: remaining accessible names ──────────────────────────────────────

def test_pane_view_up_button_accessible(qtbot) -> None:
    from biome_fm.views.pane_view import PaneView

    v = PaneView()
    qtbot.addWidget(v)
    assert v._btn_up.accessibleName() == "Up"
    assert v._bookmark_menu.accessibleName() == "Bookmarks"
    assert v.jump_bar.accessibleName() == "Type to navigate"


def test_omnibar_accessible_names(qtbot) -> None:
    from unittest.mock import Mock
    from biome_fm.presenters.omnibar_presenter import OmnibarPresenter
    from biome_fm.views.omnibar import OmniBar

    bar = OmniBar(Mock(spec=OmnibarPresenter))
    qtbot.addWidget(bar)
    assert bar._input.accessibleName() == "Omnibar input"
    assert bar._list.accessibleName() == "Omnibar results"


def test_sidebar_accessible_names(qtbot) -> None:
    from biome_fm.views.sidebar_panel import SidebarPanel

    p = SidebarPanel()
    qtbot.addWidget(p)
    assert p.accessibleName() == "Sidebar"
    assert p._tree.accessibleName() == "Sidebar navigation"


def test_filter_bar_accessible_names(qtbot) -> None:
    from biome_fm.views.filter_bar import FilterBar

    bar = FilterBar()
    qtbot.addWidget(bar)
    assert bar._edit.accessibleName() == "Filter text"
    assert bar._preset_combo.accessibleName() == "Filter presets"
    assert bar._invert_btn.accessibleName() == "Invert filter"


def test_ai_chat_panel_accessible_names(qtbot) -> None:
    from biome_fm.views.ai_chat_panel import AIChatPanel

    p = AIChatPanel()
    qtbot.addWidget(p)
    assert p.accessibleName() == "AI chat panel"
    assert p._provider_combo.accessibleName() == "AI provider"
    assert p._model_combo.accessibleName() == "AI model"
    assert p._input.accessibleName() == "Message input"
    assert p._cancel_btn.accessibleName() == "Cancel"
    assert p._log.accessibleName() == "Chat history"


def test_main_window_status_labels_accessible(qtbot) -> None:
    from biome_fm.views.main_window import MainWindow

    w = MainWindow()
    qtbot.addWidget(w)
    assert w._git_btn.accessibleName() == "Git branch"
    assert w._ops_label.accessibleName() == "Active operations"
    assert w._remote_status_label.accessibleName() == "Remote connection status"


def test_preview_panel_accessible_names(qtbot) -> None:
    from biome_fm.views.preview_panel import PreviewPanel

    p = PreviewPanel()
    qtbot.addWidget(p)
    assert p._find_edit.accessibleName() == "Find in preview"
    assert p._text_view.accessibleName() == "Preview content"
