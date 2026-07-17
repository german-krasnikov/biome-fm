"""Unit tests for PanePresenter.toggle_flat_view() — TDD red phase."""
from pathlib import Path
from unittest.mock import MagicMock, call


def _make_presenter(tmp_path: Path):
    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.pane_presenter import PanePresenter

    view = MagicMock()
    view.current_cursor_item.return_value = None
    p = PanePresenter(view=view, vfs=LocalVFS())
    p.navigate_to(tmp_path)
    view.reset_mock()
    return p, view


def test_flat_view_includes_subdir_files(tmp_path):
    """Files in subdirectories appear in flat listing."""
    (tmp_path / "a.txt").write_text("a")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("b")

    p, view = _make_presenter(tmp_path)
    p.toggle_flat_view()

    view.set_items.assert_called_once()
    items = view.set_items.call_args[0][0]
    names = {i.name for i in items}
    assert "a.txt" in names
    assert str(Path("sub") / "b.txt") in names


def test_flat_view_relative_names(tmp_path):
    """Item names are root-relative paths, not bare filenames."""
    sub = tmp_path / "foo"
    sub.mkdir()
    (sub / "bar.txt").write_text("x")

    p, view = _make_presenter(tmp_path)
    p.toggle_flat_view()

    items = view.set_items.call_args[0][0]
    assert any(i.name == str(Path("foo") / "bar.txt") for i in items)
    # no bare 'bar.txt'
    assert not any(i.name == "bar.txt" for i in items)


def test_flat_view_excludes_hidden(tmp_path):
    """Hidden files and files inside hidden dirs are excluded."""
    (tmp_path / ".secret").write_text("s")
    hidden_dir = tmp_path / ".hiddendir"
    hidden_dir.mkdir()
    (hidden_dir / "inside.txt").write_text("i")
    (tmp_path / "visible.txt").write_text("v")

    p, view = _make_presenter(tmp_path)
    p.toggle_flat_view()

    items = view.set_items.call_args[0][0]
    names = {i.name for i in items}
    assert "visible.txt" in names
    assert ".secret" not in names
    assert not any(".hiddendir" in n for n in names)


def test_flat_view_second_toggle_goes_back(tmp_path):
    """Calling toggle_flat_view while in virtual mode triggers go_back."""
    (tmp_path / "f.txt").write_text("f")

    p, view = _make_presenter(tmp_path)
    p.toggle_flat_view()

    view.reset_mock()
    p.toggle_flat_view()  # already virtual → go_back

    # go_back navigates to a real path (pops from _back)
    view.set_path.assert_called()
    called_path = view.set_path.call_args[0][0]
    assert called_path == tmp_path


def test_flat_view_empty_dir(tmp_path):
    """Empty directory produces an empty virtual view."""
    p, view = _make_presenter(tmp_path)
    p.toggle_flat_view()

    items = view.set_items.call_args[0][0]
    assert items == []

    # label contains the dir name
    label_path = view.set_path.call_args[0][0]
    assert tmp_path.name in str(label_path)
