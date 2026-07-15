"""Test that PanePresenter.refresh() preserves cursor position."""
from pathlib import Path


def test_refresh_preserves_cursor(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.file_item import FileItem

    selected = []

    class FakeView:
        def set_items(self, items): pass
        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, p): pass
        def current_cursor_item(self):
            return FileItem("b.txt", tmp_path / "b.txt", False, 0, 0.0)
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, p): pass
        def select_item(self, name): selected.append(name)

    p = PanePresenter(FakeView(), LocalVFS())
    p.navigate_to(tmp_path)
    selected.clear()
    p.refresh()
    assert selected[-1] == "b.txt"
