"""Tests for FilterBar widget."""

import pytest

from biome_fm.qt import Qt
from biome_fm.views.filter_bar import FilterBar


@pytest.fixture
def bar(qtbot):
    w = FilterBar()
    qtbot.addWidget(w)
    w.show()
    return w


def test_initially_hidden(qtbot):
    w = FilterBar()
    qtbot.addWidget(w)
    assert not w.isVisible()


def test_typing_emits_filter_changed(bar, qtbot):
    with qtbot.waitSignal(bar.filter_changed, timeout=1000) as blocker:
        bar.activate()
        bar._edit.setText("hello")
    assert blocker.args == ["hello"]


def test_activate_shows_and_focuses(bar, qtbot):
    bar.hide()
    bar.activate()
    assert bar.isVisible()
    # focus check skipped: offscreen platform doesn't propagate focus


def test_escape_clears_and_hides(bar, qtbot):
    bar.activate()
    bar._edit.setText("abc")
    qtbot.keyClick(bar._edit, Qt.Key.Key_Escape)
    assert not bar.isVisible()
    assert bar._edit.text() == ""
