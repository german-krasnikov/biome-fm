"""Test that PanePresenter.refresh() preserves cursor position and marks."""
from pathlib import Path
from unittest.mock import MagicMock


def test_refresh_preserves_marks():
    """Marks must survive refresh() — _marks set is not cleared when path == cwd."""
    from biome_fm.models.file_item import FileItem
    from biome_fm.presenters.pane_presenter import PanePresenter

    item_a = FileItem(name="a.txt", path=Path("/tmp/a.txt"), is_dir=False, size=10, modified=0.0)
    item_b = FileItem(name="b.txt", path=Path("/tmp/b.txt"), is_dir=False, size=20, modified=0.0)

    view = MagicMock()
    view.current_cursor_item.return_value = item_a

    vfs = MagicMock()
    vfs.listdir.return_value = [item_a, item_b]

    p = PanePresenter(view=view, vfs=vfs, opener=lambda _: None)
    p.navigate_to(Path("/tmp"))

    # Mark item_b
    p._marks = {str(item_b.path)}
    p._push_marks()
    view.reset_mock()

    # Refresh — reset mtime so skip-optimization doesn't suppress the call
    p._cwd_mtime = 0.0
    p.refresh()

    # Marks must be preserved in presenter state
    assert item_b.path in p.marks

    # And pushed to view
    view.set_marked.assert_called()
    last_marks = view.set_marked.call_args[0][0]
    assert item_b.path in last_marks


def test_refresh_preserves_cursor(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.file_item import FileItem

    selected = []

    class FakeView:
        def set_items(self, items, **kwargs): pass
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
    p._cwd_mtime = 0.0  # reset so refresh doesn't skip
    p.refresh()
    assert selected[-1] == "b.txt"


# ── Fix B1: preserve_scroll correctness ──────────────────────────────────────

def _make_tracking_view(tmp_path):
    """FakeView that records set_items kwargs."""
    from biome_fm.models.file_item import FileItem

    calls = []

    class TrackingView:
        set_items_calls = calls

        def set_items(self, items, **kwargs):
            calls.append((items, kwargs))

        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, p): pass
        def current_cursor_item(self):
            return FileItem("..", tmp_path, True, 0, 0.0)
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, p): pass
        def select_item(self, name): pass

    return TrackingView()


def test_preserve_scroll_false_on_navigate(tmp_path):
    """Navigating to a new dir must pass preserve_scroll=False."""
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter

    sub = tmp_path / "sub"
    sub.mkdir()
    view = _make_tracking_view(tmp_path)
    p = PanePresenter(view, LocalVFS())
    p.navigate_to(tmp_path)
    view.set_items_calls.clear()
    p.navigate_to(sub)
    _, kwargs = view.set_items_calls[-1]
    assert kwargs.get("preserve_scroll") is False


def test_preserve_scroll_true_on_refresh(tmp_path):
    """Refresh (same dir) must pass preserve_scroll=True."""
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter

    view = _make_tracking_view(tmp_path)
    p = PanePresenter(view, LocalVFS())
    p.navigate_to(tmp_path)
    view.set_items_calls.clear()
    p._cwd_mtime = 0.0  # reset so refresh doesn't skip
    p.refresh()
    _, kwargs = view.set_items_calls[-1]
    assert kwargs.get("preserve_scroll") is True
