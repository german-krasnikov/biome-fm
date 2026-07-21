"""TDD: F406 Full-screen Subshell Toggle (Ctrl+O)."""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget, QSplitter
from PySide6.QtCore import Qt

from biome_fm.views.panel_coordinator import PanelCoordinator


@pytest.fixture(scope="module")
def app():
    existing = QApplication.instance()
    return existing or QApplication([])


@pytest.fixture
def coordinator(app):
    left = QWidget()
    right = QWidget()
    terminal = QWidget()
    preview = QWidget()
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(left)
    splitter.addWidget(right)
    splitter.setSizes([400, 400])

    panels = {"terminal": terminal, "preview": preview}
    mgr = MagicMock()
    mgr.state.return_value = MagicMock(value="hidden")

    coord = PanelCoordinator(mgr, panels, left, right, splitter, QWidget())
    # make all visible by default
    left.show()
    right.show()
    terminal.show()
    preview.show()
    yield coord, left, right, terminal, preview


def test_enter_fullscreen_shell_hides_panes(coordinator):
    coord, left, right, terminal, preview = coordinator
    coord.toggle_fullscreen_shell()
    assert left.isHidden()
    assert right.isHidden()


def test_enter_fullscreen_shell_terminal_visible(coordinator):
    coord, left, right, terminal, preview = coordinator
    coord._shell_mode = False  # reset
    coord.toggle_fullscreen_shell()
    assert not terminal.isHidden()


def test_enter_fullscreen_shell_other_panels_hidden(coordinator):
    coord, left, right, terminal, preview = coordinator
    coord._shell_mode = False
    coord.toggle_fullscreen_shell()
    assert preview.isHidden()


def test_exit_fullscreen_shell_restores_panes(coordinator):
    coord, left, right, terminal, preview = coordinator
    coord._shell_mode = False
    left.show(); right.show()
    coord.toggle_fullscreen_shell()  # enter
    coord.toggle_fullscreen_shell()  # exit
    assert not left.isHidden()
    assert not right.isHidden()


def test_toggle_idempotent(coordinator):
    coord, left, right, terminal, preview = coordinator
    coord._shell_mode = False
    coord.toggle_fullscreen_shell()
    coord.toggle_fullscreen_shell()
    assert not coord.shell_mode


def test_exit_restores_panel_visibility(coordinator):
    coord, left, right, terminal, preview = coordinator
    # preview hidden before entering shell mode
    preview.hide()
    terminal.hide()
    coord._shell_mode = False
    coord.toggle_fullscreen_shell()   # enter — terminal forced visible
    coord.toggle_fullscreen_shell()   # exit — should restore pre-enter visibility
    assert preview.isHidden()         # was hidden before, stays hidden
    assert terminal.isHidden()        # was hidden before, stays hidden
