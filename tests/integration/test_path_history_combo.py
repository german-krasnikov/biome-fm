"""Integration tests for path history combo box in PaneView."""
from pathlib import Path

import pytest

from biome_fm.views.pane_view import PaneView


@pytest.fixture
def pane(qtbot):
    w = PaneView()
    qtbot.addWidget(w)
    return w


def test_set_nav_history_populates_combo(pane):
    paths = [Path("/a"), Path("/b"), Path("/c")]
    pane.set_nav_history(paths)
    assert pane._path_bar.count() == 3


def test_set_path_updates_lineedit(pane):
    pane.set_path(Path("/foo/bar"))
    assert pane._path_bar.lineEdit().text() == "/foo/bar"


def test_combo_activated_emits_path_change(pane, qtbot):
    pane.set_nav_history([Path("/tmp/test")])
    with qtbot.waitSignal(pane.path_change_requested, timeout=1000) as sig:
        pane._path_bar.setCurrentIndex(0)
        pane._path_bar.activated.emit(0)
    assert sig.args[0] == Path("/tmp/test")
