"""Integration test: back/forward nav buttons have custom context menu."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from biome_fm.qt import Qt
from biome_fm.views.pane_view import PaneView


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    v.show()
    return v


def test_back_button_has_context_menu(view) -> None:
    assert hasattr(view, "_btn_back")
    policy = view._btn_back.contextMenuPolicy()
    assert policy == Qt.ContextMenuPolicy.CustomContextMenu


def test_forward_button_has_context_menu(view) -> None:
    assert hasattr(view, "_btn_fwd")
    policy = view._btn_fwd.contextMenuPolicy()
    assert policy == Qt.ContextMenuPolicy.CustomContextMenu
