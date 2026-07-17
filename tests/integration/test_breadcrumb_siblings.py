"""Integration tests for breadcrumb sibling dropdown (Feature #39)."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu

from biome_fm.views.breadcrumb_bar import BreadcrumbBar, _SegmentButton


def _capture_context_menu(btn: _SegmentButton) -> QMenu:
    """Trigger contextMenuEvent and return the QMenu without showing it."""
    captured: list[QMenu] = []

    def fake_popup(self, pos, action=None):
        captured.append(self)

    with patch.object(QMenu, "popup", fake_popup):
        ev = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, QPoint(0, 0))
        btn.contextMenuEvent(ev)

    assert captured, "contextMenuEvent did not call QMenu.popup"
    return captured[0]


def _segment(bar: BreadcrumbBar, label: str) -> _SegmentButton:
    return next(b for b in bar.findChildren(_SegmentButton) if b.text() == label)


@pytest.fixture
def sibling_tree(tmp_path):
    """parent/alpha, parent/beta, parent/gamma — bar navigated to beta."""
    parent = tmp_path / "parent"
    for name in ("alpha", "beta", "gamma"):
        (parent / name).mkdir(parents=True)
    return parent


@pytest.fixture
def bar(qtbot, sibling_tree):
    b = BreadcrumbBar()
    qtbot.addWidget(b)
    b.show()
    b.set_path(sibling_tree / "beta")
    return b


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_context_menu_has_siblings_submenu(bar):
    btn = _segment(bar, "beta")
    menu = _capture_context_menu(btn)
    titles = [a.text() for a in menu.actions()]
    assert "Siblings" in titles


def test_sibling_action_emits_navigated(bar, qtbot, sibling_tree):
    btn = _segment(bar, "beta")
    menu = _capture_context_menu(btn)

    siblings_action = next(a for a in menu.actions() if a.text() == "Siblings")
    sub = siblings_action.menu()
    assert sub is not None

    alpha_action = next(a for a in sub.actions() if "alpha" in a.text())

    with qtbot.waitSignal(btn.navigated, timeout=1000) as sig:
        alpha_action.trigger()

    assert sig.args[0] == sibling_tree / "alpha"


def test_no_siblings_menu_at_root(qtbot):
    bar = BreadcrumbBar()
    qtbot.addWidget(bar)
    bar.show()
    bar.set_path(Path("/"))
    root_btn = bar.findChildren(_SegmentButton)[0]
    menu = _capture_context_menu(root_btn)
    titles = [a.text() for a in menu.actions()]
    assert "Siblings" not in titles


def test_current_segment_marked(bar, sibling_tree):
    btn = _segment(bar, "beta")
    menu = _capture_context_menu(btn)

    siblings_action = next(a for a in menu.actions() if a.text() == "Siblings")
    sub = siblings_action.menu()
    assert sub is not None

    sub_texts = [a.text() for a in sub.actions()]
    assert any(t.startswith("▶") and "beta" in t for t in sub_texts), sub_texts
    # siblings without ▶
    assert any("alpha" in t and not t.startswith("▶") for t in sub_texts)
