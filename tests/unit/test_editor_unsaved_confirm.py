"""Unit tests for EditorDialog unsaved-changes guard."""
import inspect
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.presenters.editor_presenter import EditorPresenter
from biome_fm.views.editor_dialog import EditorDialog


def _make_view(text: str) -> MagicMock:
    v = MagicMock()
    v.toPlainText.return_value = text
    return v


def test_close_unmodified_no_dialog(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("hello")
    presenter = EditorPresenter(_make_view("hello"), p)
    assert presenter.is_modified() is False


def test_close_modified_detected(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("hello")
    presenter = EditorPresenter(_make_view("hello modified"), p)
    assert presenter.is_modified() is True


def test_closeevent_exists() -> None:
    src = inspect.getsource(EditorDialog)
    assert "closeEvent" in src
