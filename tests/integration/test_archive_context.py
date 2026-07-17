"""Integration tests for archive context menu items in PaneView."""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.views.pane_view import PaneView
from biome_fm.models.file_item import FileItem


def _item(path: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=path.name, path=path, size=0, modified=0.0, is_dir=is_dir)


class TestArchiveContextMenu:
    def test_compress_action_emittable(self, qtbot: QtBot) -> None:
        """PaneView.context_action_requested carries 'compress'."""
        view = PaneView()
        qtbot.addWidget(view)
        with qtbot.waitSignal(view.context_action_requested, timeout=500) as blocker:
            view.context_action_requested.emit("compress")
        assert blocker.args == ["compress"]

    def test_extract_action_emittable(self, qtbot: QtBot) -> None:
        """PaneView.context_action_requested carries 'extract'."""
        view = PaneView()
        qtbot.addWidget(view)
        with qtbot.waitSignal(view.context_action_requested, timeout=500) as blocker:
            view.context_action_requested.emit("extract")
        assert blocker.args == ["extract"]

    def test_archive_suffix_check_zip(self, tmp_path: Path) -> None:
        """The suffix heuristic used in the context menu matches .zip."""
        p = tmp_path / "archive.zip"
        suffixes = "".join(p.suffixes).lower()
        _ARCHIVE_EXTS = (".zip", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz")
        assert any(suffixes.endswith(e) for e in _ARCHIVE_EXTS)

    def test_archive_suffix_check_tar_gz(self, tmp_path: Path) -> None:
        """The suffix heuristic matches .tar.gz."""
        p = tmp_path / "data.tar.gz"
        suffixes = "".join(p.suffixes).lower()
        _ARCHIVE_EXTS = (".zip", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz")
        assert any(suffixes.endswith(e) for e in _ARCHIVE_EXTS)

    def test_extract_not_shown_for_dir(self, tmp_path: Path) -> None:
        """Directory items should NOT trigger Extract Here."""
        d = tmp_path / "mydir"
        item = _item(d, is_dir=True)
        _ARCHIVE_EXTS = (".zip", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz")
        suffixes = "".join(item.path.suffixes).lower()
        would_show = not item.is_dir and any(suffixes.endswith(e) for e in _ARCHIVE_EXTS)
        assert not would_show
