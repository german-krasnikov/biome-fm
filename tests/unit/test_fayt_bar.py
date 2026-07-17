"""TDD: FAYT multi-mode bar signal routing."""
from __future__ import annotations

import pytest


@pytest.fixture()
def bar(qtbot):
    from biome_fm.views.fayt_bar import FAYTBar

    w = FAYTBar()
    qtbot.addWidget(w)
    return w


def test_no_prefix_filters(bar, qtbot) -> None:
    with qtbot.waitSignal(bar.filter_changed, timeout=500) as blocker:
        bar._input.setText("foo")
        bar._input.textChanged.emit("foo")
    assert blocker.args == ["foo"]


def test_slash_navigates(bar, qtbot) -> None:
    with qtbot.waitSignal(bar.navigate_requested, timeout=500) as blocker:
        bar._input.setText("/home")
        bar._input.textChanged.emit("/home")
    assert blocker.args == ["home"]


def test_colon_commands(bar, qtbot) -> None:
    with qtbot.waitSignal(bar.command_requested, timeout=500) as blocker:
        bar._input.setText(":sort")
        bar._input.textChanged.emit(":sort")
    assert blocker.args == ["sort"]


def test_question_searches(bar, qtbot) -> None:
    with qtbot.waitSignal(bar.search_requested, timeout=500) as blocker:
        bar._input.setText("?report")
        bar._input.textChanged.emit("?report")
    assert blocker.args == ["report"]
