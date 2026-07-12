"""Tests for JumpBar widget."""

import pytest

from biome_fm.views.jump_bar import JumpBar


@pytest.fixture
def bar(qtbot):
    w = JumpBar()
    qtbot.addWidget(w)
    return w


def test_initially_hidden(bar):
    assert not bar.isVisible()


def test_append_shows_and_emits(bar, qtbot):
    with qtbot.waitSignal(bar.jump_text_changed, timeout=1000) as blocker:
        bar.append_char("a")
    assert bar.isVisible()
    assert blocker.args == ["a"]


def test_clear_hides(bar, qtbot):
    bar.append_char("x")
    bar.clear()
    assert not bar.isVisible()
