"""Tests for Workspaces moved into View menu submenu (Issue 7)."""

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMenu

from biome_fm.views.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def win(app):
    w = MainWindow()
    yield w
    w.close()


def test_no_standalone_ws_button(win):
    assert not hasattr(win, "_ws_btn")


def test_workspace_menu_attribute_exists(win):
    assert hasattr(win, "workspace_menu")


def test_workspace_menu_is_submenu(win):
    ws_menu = win.workspace_menu
    assert isinstance(ws_menu, QMenu)
    # Must be a child submenu of View menu — check by identity
    mb = win.menuBar()
    mb_actions = list(mb.actions())  # strong ref
    view_action = next((a for a in mb_actions if "View" in a.text()), None)
    assert view_action is not None, "View menu not found"
    view_menu = view_action.menu()
    assert view_menu is not None
    vm_actions = list(view_menu.actions())  # strong ref
    assert any(a.menu() is ws_menu for a in vm_actions), \
        "workspace_menu not found as submenu in View menu"
