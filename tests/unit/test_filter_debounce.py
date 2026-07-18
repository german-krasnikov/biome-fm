"""F327 — Filter Debounce: 200ms debounce on filter_changed signal."""

from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from biome_fm.qt import QApplication, QTimer


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestFilterDebounce:
    def test_debounce_timer_created(self, qapp):
        from biome_fm.views.filter_bar import FilterBar
        bar = FilterBar()
        assert hasattr(bar, "_debounce")
        assert isinstance(bar._debounce, QTimer)
        assert bar._debounce.isSingleShot()

    def test_clear_emits_immediately(self, qapp):
        from biome_fm.views.filter_bar import FilterBar
        bar = FilterBar()
        # set some text first
        bar._edit.setText("foo")
        received: list[str] = []
        bar.filter_changed.connect(received.append)
        # clearing should emit immediately (not debounced)
        bar._edit.clear()
        assert "" in received
