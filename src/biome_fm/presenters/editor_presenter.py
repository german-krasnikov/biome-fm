"""EditorPresenter — logic for the built-in text editor (Feature #18)."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class _EditorView(Protocol):
    def toPlainText(self) -> str: ...
    def setPlainText(self, text: str) -> None: ...


class EditorPresenter:
    def __init__(self, view: _EditorView, path: Path) -> None:
        self._view = view
        self._path = path
        self._saved_text: str = path.read_text(errors="replace") if path.exists() else ""

    def save(self) -> None:
        text = self._view.toPlainText()
        self._path.write_text(text)
        self._saved_text = text

    def is_modified(self) -> bool:
        return self._view.toPlainText() != self._saved_text
