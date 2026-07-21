"""F435 — Detachable Shell with Selection Env Vars."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtCore import QProcess


@pytest.fixture()
def panel(qtbot, monkeypatch):
    from biome_fm.views.terminal_panel import TerminalPanel

    monkeypatch.setattr(QProcess, "start", lambda *a, **k: None)
    tp = TerminalPanel()
    qtbot.addWidget(tp)
    return tp


def test_start_sets_biome_cwd(panel, tmp_path):
    panel.start(tmp_path)
    assert panel._proc.processEnvironment().value("BIOME_CWD") == str(tmp_path)


def test_start_sets_biome_selected(panel, tmp_path):
    panel.start(tmp_path, selected=[Path("/a"), Path("/b")])
    assert panel._proc.processEnvironment().value("BIOME_SELECTED") == "/a\n/b"


def test_start_sets_biome_cursor(panel, tmp_path):
    panel.start(tmp_path, cursor=Path("/x/y"))
    assert panel._proc.processEnvironment().value("BIOME_CURSOR") == "/x/y"


def test_start_empty_selected_is_empty_string(panel, tmp_path):
    panel.start(tmp_path)
    assert panel._proc.processEnvironment().value("BIOME_SELECTED") == ""


def test_start_no_cursor_is_empty_string(panel, tmp_path):
    panel.start(tmp_path)
    assert panel._proc.processEnvironment().value("BIOME_CURSOR") == ""
