"""SearchResultsPanel integration tests."""
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.qt import QPushButton
from biome_fm.views.search_panel import SearchResultsPanel


def _result(name="foo.txt"):
    return SearchResult(
        item=FileItem(name=name, path=Path("/tmp") / name, is_dir=False, size=100, modified=1000.0)
    )


@pytest.fixture
def panel(qtbot):
    p = SearchResultsPanel()
    qtbot.addWidget(p)
    p.show()
    return p


def test_on_search_started_clears_and_shows_progress(panel):
    panel.add_result(_result())
    assert panel._model.rowCount() == 1
    panel.on_search_started("*.py")
    assert panel._model.rowCount() == 0
    assert panel._progress.isVisible()
    assert panel._stop_btn.isVisible()


def test_add_result_increments_count(panel):
    panel.on_search_started("*.txt")
    panel.add_result(_result("a.txt"))
    panel.add_result(_result("b.txt"))
    assert panel._model.rowCount() == 2
    assert "2" in panel._status.text()


def test_on_finished_hides_progress(panel):
    panel.on_search_started("test")
    panel.on_finished(5)
    assert not panel._progress.isVisible()
    assert not panel._stop_btn.isVisible()
    assert "5" in panel._status.text()


def test_close_button_emits_signal(panel, qtbot):
    with qtbot.waitSignal(panel.close_requested, timeout=1000):
        for child in panel.findChildren(QPushButton):
            if child.text() == "✕":
                child.click()
                break


def test_stop_button_emits_signal(panel, qtbot):
    panel.on_search_started("test")
    with qtbot.waitSignal(panel.stop_requested, timeout=1000):
        panel._stop_btn.click()


def test_double_click_emits_navigate(panel, qtbot):
    panel.on_search_started("test")
    panel.add_result(_result("target.py"))
    with qtbot.waitSignal(panel.navigate_to_file, timeout=1000):
        idx = panel._model.index(0, 0)
        panel._table.doubleClicked.emit(idx)


def test_on_cancelled_shows_status(panel):
    panel.on_search_started("test")
    panel.add_result(_result())
    panel.on_cancelled()
    assert not panel._progress.isVisible()
    assert "Cancelled" in panel._status.text()


# F224 — Search Result Columns
def test_search_results_model_has_four_columns():
    from biome_fm.views.search_panel import SearchResultsModel
    model = SearchResultsModel()
    assert model.columnCount() == 4
    assert model.HEADERS == ("Name", "Location", "Size", "Modified")
