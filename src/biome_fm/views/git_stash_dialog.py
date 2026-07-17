"""Git Stash Manager dialog."""
from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from biome_fm.preview.providers._git_helpers import run_git


def parse_stash_list(raw: str) -> list[str]:
    """Parse `git stash list` output into list of stash refs."""
    return [line for line in raw.splitlines() if line.strip()]


class GitStashDialog(QDialog):
    """View-only: emits signals, presenter handles git logic."""

    stash_apply = Signal(str)
    stash_pop = Signal(str)
    stash_drop = Signal(str)
    stash_new = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Git Stash Manager")
        self.resize(500, 300)

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        for label, sig_name in [
            ("Apply", "_apply"),
            ("Pop", "_pop"),
            ("Drop", "_drop"),
            ("New…", "_new"),
            ("Refresh", "_refresh_click"),
        ]:
            b = QPushButton(label)
            b.clicked.connect(getattr(self, sig_name))
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

    def set_items(self, items: list[str]) -> None:
        self._list.clear()
        for item in items:
            self._list.addItem(item)

    def _selected_ref(self) -> str | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.text().split(":")[0].strip()

    def _apply(self) -> None:
        ref = self._selected_ref()
        if ref:
            self.stash_apply.emit(ref)

    def _pop(self) -> None:
        ref = self._selected_ref()
        if ref:
            self.stash_pop.emit(ref)

    def _drop(self) -> None:
        ref = self._selected_ref()
        if ref:
            self.stash_drop.emit(ref)

    def _new(self) -> None:
        msg, ok = QInputDialog.getText(self, "New Stash", "Message:")
        if ok:
            self.stash_new.emit(msg.strip())

    def _refresh_click(self) -> None:
        self.refresh_requested.emit()


class GitStashPresenter:
    """Presenter: owns git stash logic, drives the view."""

    def __init__(self, view: GitStashDialog, repo: Path) -> None:
        self._view = view
        self._repo = repo
        view.stash_apply.connect(lambda ref: self._run(["stash", "apply", ref]))
        view.stash_pop.connect(lambda ref: self._run(["stash", "pop", ref]))
        view.stash_drop.connect(lambda ref: self._run(["stash", "drop", ref]))
        view.stash_new.connect(self._new)
        view.refresh_requested.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        try:
            raw = run_git(["stash", "list"], self._repo, timeout=10)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError):
            raw = ""
        self._view.set_items(parse_stash_list(raw))

    def _run(self, args: list[str]) -> None:
        try:
            run_git(args, self._repo, timeout=10)
            self.refresh()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError):
            pass

    def _new(self, msg: str) -> None:
        args = ["stash", "push"]
        if msg:
            args += ["-m", msg]
        self._run(args)
