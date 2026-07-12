"""Tests for hidden file filtering in DirSortFilterProxy."""
from pathlib import Path

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _make_items():
    return [
        FileItem(name="..", path=Path("/parent"), is_dir=True, size=0, modified=0.0),
        FileItem(name="visible.txt", path=Path("/visible.txt"), is_dir=False, size=100, modified=0.0),
        FileItem(name=".hidden", path=Path("/.hidden"), is_dir=False, size=50, modified=0.0),
        FileItem(name=".git", path=Path("/.git"), is_dir=True, size=0, modified=0.0),
        FileItem(name="normal_dir", path=Path("/normal_dir"), is_dir=True, size=0, modified=0.0),
    ]


def test_hidden_files_hidden_by_default(qtbot):
    """Hidden files should be filtered out when show_hidden=False."""
    model = DirectoryModel()
    proxy = DirSortFilterProxy()
    proxy.setSourceModel(model)
    model.set_items(_make_items())
    visible = [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]
    assert ".hidden" not in visible
    assert ".git" not in visible
    assert ".." in visible
    assert "visible.txt" in visible


def test_show_hidden_shows_all(qtbot):
    """When show_hidden=True, all files visible."""
    model = DirectoryModel()
    proxy = DirSortFilterProxy()
    proxy.setSourceModel(model)
    model.set_items(_make_items())
    proxy.set_show_hidden(True)
    visible = [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]
    assert ".hidden" in visible
    assert ".git" in visible


def test_toggle_hidden_invalidates_filter(qtbot):
    """Toggling hidden should update visible rows."""
    model = DirectoryModel()
    proxy = DirSortFilterProxy()
    proxy.setSourceModel(model)
    model.set_items(_make_items())
    assert proxy.rowCount() == 3  # .., visible.txt, normal_dir
    proxy.set_show_hidden(True)
    assert proxy.rowCount() == 5


def test_filter_and_hidden_combined(qtbot):
    """Text filter + hidden filter should work together."""
    model = DirectoryModel()
    proxy = DirSortFilterProxy()
    proxy.setSourceModel(model)
    model.set_items(_make_items())
    proxy.set_filter("vis")
    assert proxy.rowCount() == 2  # .. + visible.txt
    proxy.set_show_hidden(True)
    proxy.set_filter("")
    assert proxy.rowCount() == 5
