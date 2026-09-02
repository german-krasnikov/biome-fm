"""Unit tests for EditorPresenter (Feature #18)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.presenters.editor_presenter import EditorPresenter


class _MockEditorView:
    def __init__(self, text: str = "") -> None:
        self._text = text

    def toPlainText(self) -> str:
        return self._text

    def setPlainText(self, text: str) -> None:
        self._text = text


def test_save_writes_file(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("original")
    view = _MockEditorView("modified content")
    presenter = EditorPresenter(view, f)
    presenter.save()
    assert f.read_text() == "modified content"


def test_is_modified(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("hello")
    view = _MockEditorView("hello")
    presenter = EditorPresenter(view, f)
    assert not presenter.is_modified()
    view.setPlainText("hello changed")
    assert presenter.is_modified()


def test_save_is_atomic(tmp_path: Path) -> None:
    f = tmp_path / "data.txt"
    f.write_text("original")
    view = _MockEditorView("modified")
    presenter = EditorPresenter(view, f)
    # Simulate crash on rename — original must survive
    with patch("pathlib.Path.replace", side_effect=OSError("disk full")), pytest.raises(OSError):
        presenter.save()
    assert f.read_text() == "original"
