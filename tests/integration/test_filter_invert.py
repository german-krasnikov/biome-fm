"""Integration tests for FilterBar inversion button (F228)."""
from __future__ import annotations

from biome_fm.views.filter_bar import FilterBar


def test_invert_button_exists(qtbot):
    bar = FilterBar()
    qtbot.addWidget(bar)
    bar.activate()
    assert hasattr(bar, "_invert_btn")
    assert bar._invert_btn.isCheckable()
    assert bar._invert_btn.text() == "¬"


def test_invert_button_emits_signal(qtbot):
    bar = FilterBar()
    qtbot.addWidget(bar)
    bar.activate()
    signals = []
    bar.invert_toggled.connect(signals.append)
    bar._invert_btn.setChecked(True)
    assert signals == [True]
    bar._invert_btn.setChecked(False)
    assert signals == [True, False]


def test_deactivate_resets_invert(qtbot):
    bar = FilterBar()
    qtbot.addWidget(bar)
    bar.activate()
    bar._invert_btn.setChecked(True)
    bar.deactivate()
    assert not bar._invert_btn.isChecked()
