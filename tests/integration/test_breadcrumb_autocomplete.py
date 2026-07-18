"""F302 — Breadcrumb remote path autocomplete tests."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest

from biome_fm.views.breadcrumb_bar import BreadcrumbBar


@pytest.fixture
def bar(qtbot):
    b = BreadcrumbBar()
    qtbot.addWidget(b)
    b.show()
    return b


class TestBreadcrumbAutocomplete:
    def test_default_completer_is_filesystem(self, bar):
        """No custom source → QFileSystemModel completer in place."""
        from PySide6.QtWidgets import QFileSystemModel
        completer = bar._combo.lineEdit().completer()
        assert completer is not None
        assert isinstance(completer.model(), QFileSystemModel)

    def test_set_completer_source_none_restores_default(self, bar):
        """set_completer_source(None) keeps or restores filesystem completer."""
        from PySide6.QtWidgets import QFileSystemModel
        bar.set_completer_source(None)
        completer = bar._combo.lineEdit().completer()
        assert completer is not None
        assert isinstance(completer.model(), QFileSystemModel)

    def test_remote_calls_source_fn(self, qtbot, bar):
        """set_completer_source(fn) → fn called when text changes."""
        called_with: list[str] = []

        def source(text: str) -> list[str]:
            called_with.append(text)
            return ["sftp://host/dir1", "sftp://host/dir2"]

        bar.set_completer_source(source)
        bar.activate_edit()
        bar._combo.lineEdit().setText("sftp://host/")
        qtbot.wait(50)  # allow QTimer.singleShot(0) to fire
        assert len(called_with) >= 1
        assert "sftp://host/" in called_with

    def test_set_completer_source_replaces_previous(self, qtbot, bar):
        """Calling set_completer_source twice — last one wins."""
        calls_a: list[str] = []
        calls_b: list[str] = []

        bar.set_completer_source(lambda t: (calls_a.append(t) or []))  # type: ignore[func-returns-value]
        bar.set_completer_source(lambda t: (calls_b.append(t) or []))  # type: ignore[func-returns-value]
        bar.activate_edit()
        bar._combo.lineEdit().setText("sftp://host/x")
        qtbot.wait(50)
        assert len(calls_b) >= 1
        # first fn not called after replacement
        assert len(calls_a) == 0
