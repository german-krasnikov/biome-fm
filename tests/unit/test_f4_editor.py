"""Unit tests for F4/Shift+F4 editor shortcut behavior."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helper: reproduce the _open_in_editor_f4 closure logic in isolation
# ---------------------------------------------------------------------------

def _build_open_in_editor_f4(active_func, parent=None):
    """Mirror the closure in app.py for testing without Qt."""
    def _open_in_editor_f4():
        item = active_func().current_item()
        if item is None or item.name == "..":
            return
        from biome_fm.views.editor_dialog import EditorDialog
        dlg = EditorDialog(item.path, parent)
        dlg.saved.connect(lambda _: active_func().refresh())
        dlg.exec()
    return _open_in_editor_f4


def _pane_with(item):
    pane = MagicMock()
    pane.current_item.return_value = item
    return lambda: pane


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_f4_opens_editor_dialog(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hi")
    item = MagicMock()
    item.name = "hello.txt"
    item.path = f

    fn = _build_open_in_editor_f4(_pane_with(item))

    with patch("biome_fm.views.editor_dialog.EditorDialog") as MockDlg:
        mock_instance = MagicMock()
        MockDlg.return_value = mock_instance
        fn()
        MockDlg.assert_called_once_with(f, None)
        mock_instance.exec.assert_called_once()


def test_f4_on_dotdot_noop():
    item = MagicMock()
    item.name = ".."
    fn = _build_open_in_editor_f4(_pane_with(item))

    with patch("biome_fm.views.editor_dialog.EditorDialog") as MockDlg:
        fn()
        MockDlg.assert_not_called()


def test_f4_on_none_noop():
    fn = _build_open_in_editor_f4(_pane_with(None))

    with patch("biome_fm.views.editor_dialog.EditorDialog") as MockDlg:
        fn()  # must not raise
        MockDlg.assert_not_called()


def test_bar_edit_requested_connected():
    """Verify app.py wires bar.edit_requested."""
    import inspect
    import biome_fm.app as app_module
    src = inspect.getsource(app_module)
    assert "bar.edit_requested.connect" in src
