"""Integration tests for FuzzyFinder widget."""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from biome_fm.views.fuzzy_finder import FuzzyFinder


@pytest.fixture
def finder(qtbot, tmp_path):
    w = FuzzyFinder()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def root_with_files(tmp_path):
    (tmp_path / "alpha.py").write_text("x")
    (tmp_path / "beta.txt").write_text("x")
    return tmp_path


def test_overlay_shown_on_open(finder, qtbot, root_with_files):
    finder.open(root_with_files)
    assert finder.isVisible()
    finder.hide()


def test_escape_hides(finder, qtbot, root_with_files):
    finder.open(root_with_files)
    assert finder.isVisible()
    QTest.keyPress(finder, Qt.Key.Key_Escape)
    assert not finder.isVisible()


def test_enter_emits_file_chosen(finder, qtbot, root_with_files):
    from biome_fm.presenters.fuzzy_presenter import FuzzyMatch

    finder.open(root_with_files)
    # Wait for scan to complete (drain timer fires every 100ms)
    qtbot.waitUntil(lambda: finder._list.count() > 0, timeout=3000)

    with qtbot.waitSignal(finder.file_chosen, timeout=1000):
        QTest.keyPress(finder._input, Qt.Key.Key_Return)


def test_list_filters_on_query(finder, qtbot, root_with_files):
    finder.open(root_with_files)
    # Wait for files to load
    qtbot.waitUntil(lambda: finder._list.count() > 0, timeout=3000)

    initial_count = finder._list.count()

    # Type a query that matches only one file
    QTest.keyClicks(finder._input, "alpha")
    # Wait for debounce (150ms) + redraw
    qtbot.waitUntil(lambda: finder._list.count() < initial_count, timeout=2000)

    assert finder._list.count() >= 1
    assert "alpha" in finder._list.item(0).text().lower()
