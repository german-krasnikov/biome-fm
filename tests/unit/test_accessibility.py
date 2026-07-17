"""TDD: Accessible names on key widgets."""
from __future__ import annotations

import pytest


def test_pane_has_accessible_name(qtbot) -> None:
    from biome_fm.views.pane_view import PaneView

    w = PaneView()
    qtbot.addWidget(w)
    assert w._table.accessibleName() == "File list"


def test_preview_panel_has_accessible_name(qtbot) -> None:
    from biome_fm.views.preview_panel import PreviewPanel

    w = PreviewPanel()
    qtbot.addWidget(w)
    assert w.accessibleName() == "Preview panel"


def test_breadcrumb_bar_has_accessible_name(qtbot) -> None:
    from biome_fm.views.breadcrumb_bar import BreadcrumbBar

    w = BreadcrumbBar()
    qtbot.addWidget(w)
    assert w.accessibleName() == "Path navigation"


def test_search_query_has_accessible_name(qtbot, tmp_path) -> None:
    from biome_fm.views.search_dialog import SearchDialog

    w = SearchDialog(tmp_path)
    qtbot.addWidget(w)
    assert w._query.accessibleName() == "Search query"


def test_terminal_output_has_accessible_name(qtbot) -> None:
    from biome_fm.views.terminal_panel import TerminalPanel

    w = TerminalPanel()
    qtbot.addWidget(w)
    assert w._out.accessibleName() == "Terminal"
