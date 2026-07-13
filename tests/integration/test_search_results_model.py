"""SearchResultsModel unit tests."""
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult


def _result(name="foo.txt", parent="/home/user", size=100, modified=1000.0):
    return SearchResult(
        item=FileItem(name=name, path=Path(parent) / name, is_dir=False, size=size, modified=modified)
    )


def test_model_import():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    assert m.rowCount() == 0


def test_append_increments_rowcount():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    m.append(_result())
    assert m.rowCount() == 1


def test_append_batch():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    m.append_batch([_result("a.txt"), _result("b.txt"), _result("c.txt")])
    assert m.rowCount() == 3


def test_clear_resets():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    m.append(_result())
    m.clear()
    assert m.rowCount() == 0


def test_result_at():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    r = _result("bar.py")
    m.append(r)
    assert m.result_at(0) is r
    assert m.result_at(1) is None
    assert m.result_at(-1) is None


def test_data_columns():
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    m.append(_result("bar.py", "/home/user", 1024, 1700000000.0))
    assert m.data(m.index(0, 0)) == "bar.py"
    assert m.data(m.index(0, 1)) == "/home/user"
    assert m.data(m.index(0, 2)) == "1.0 KB"
    modified = m.data(m.index(0, 3))
    assert modified and len(modified) > 0


def test_header_data():
    from biome_fm.qt import Qt
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    assert m.headerData(0, Qt.Orientation.Horizontal) == "Name"
    assert m.headerData(1, Qt.Orientation.Horizontal) == "Location"


def test_tooltip_shows_full_path():
    from biome_fm.qt import Qt
    from biome_fm.views.search_panel import SearchResultsModel
    m = SearchResultsModel()
    m.append(_result("foo.txt", "/home/user"))
    tooltip = m.data(m.index(0, 0), Qt.ItemDataRole.ToolTipRole)
    assert "/home/user/foo.txt" in str(tooltip)
