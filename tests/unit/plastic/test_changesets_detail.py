"""TDD tests for Batch D — CSDetailWidget, CSDiffFileModel, set_cs_files drain."""
from __future__ import annotations

import os
import queue
from datetime import datetime

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ── CSDiffFileModel (no event loop needed) ────────────────────────────────────

def test_cs_diff_file_model_reset():
    from biome_fm.plastic._components import CSDiffFileModel
    from biome_fm.plastic._models import CSDiffFile
    m = CSDiffFileModel()
    m.reset([CSDiffFile("/a.py", "M", 3, 1, "diff text")])
    assert m.rowCount() == 1
    assert m.data(m.index(0, 1)) == "/a.py"
    assert m.data(m.index(0, 2)) == "+3"
    assert m.data(m.index(0, 3)) == "−1"


def test_cs_diff_file_model_foreground_role():
    from biome_fm.plastic._components import CSDiffFileModel
    from biome_fm.plastic._models import CSDiffFile
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    m = CSDiffFileModel()
    m.reset([CSDiffFile("/a.py", "A", 2, 0, "")])
    color = m.data(m.index(0, 0), Qt.ItemDataRole.ForegroundRole)
    assert isinstance(color, QColor)


# ── ChangesetModel tooltip ────────────────────────────────────────────────────

def test_changeset_model_tooltip():
    from biome_fm.plastic._components import ChangesetModel
    from biome_fm.plastic._models import Changeset
    from PySide6.QtCore import Qt
    m = ChangesetModel()
    m.reset([Changeset(1, datetime(2026, 1, 1), "alice", "/main", "fix bug here")])
    tip = m.data(m.index(0, 4), Qt.ItemDataRole.ToolTipRole)
    assert tip == "fix bug here"


# ── CSDetailWidget (needs QApplication) ──────────────────────────────────────

def test_cs_detail_load_cs(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import Changeset
    w = CSDetailWidget()
    cs = Changeset(42, datetime(2026, 1, 1), "alice", "/main", "fix bug")
    w.load_cs(cs)
    text = w._meta.text()
    assert "CS#42" in text
    assert "alice" in text
    assert "fix bug" in text


def test_cs_detail_load_cs_escapes_html(qapp):
    """User-supplied fields must not be injected as raw HTML."""
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import Changeset
    w = CSDetailWidget()
    cs = Changeset(1, datetime(2026, 1, 1), "<b>xss</b>", "</i>branch", "<script>evil</script>")
    w.load_cs(cs)
    text = w._meta.text()
    assert "<script>" not in text
    assert "&lt;b&gt;" in text or "&lt;script&gt;" in text


def test_cs_detail_load_files_selects_first(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import CSDiffFile
    w = CSDetailWidget()
    files = [CSDiffFile("/a.py", "M", 1, 0, "diff chunk A")]
    w.load_files(files)
    assert w._file_model.rowCount() == 1
    assert w._diff_view.toPlainText() == "diff chunk A"


def test_cs_detail_clear(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import Changeset, CSDiffFile
    w = CSDetailWidget()
    w.load_cs(Changeset(1, datetime(2026, 1, 1), "x", "/m", "c"))
    w.load_files([CSDiffFile("/a.py", "M", 1, 0, "d")])
    w.clear()
    assert w._meta.text() == ""
    assert w._file_model.rowCount() == 0


# ── ChangesetModel — no bold, multi-column tooltips, short date ──────────────

def test_changeset_model_no_bold_on_cs_column():
    from biome_fm.plastic._components import ChangesetModel
    from biome_fm.plastic._models import Changeset
    from PySide6.QtCore import Qt
    m = ChangesetModel()
    m.reset([Changeset(1, datetime(2026, 1, 1), "alice", "/main", "msg")])
    font = m.data(m.index(0, 0), Qt.ItemDataRole.FontRole)
    assert font is None


def test_changeset_model_tooltips_all_columns():
    from biome_fm.plastic._components import ChangesetModel, _DT_FMT
    from biome_fm.plastic._models import Changeset
    from PySide6.QtCore import Qt
    dt = datetime(2026, 1, 25, 14, 32)
    m = ChangesetModel()
    m.reset([Changeset(1, dt, "alice", "/main", "fix bug")])
    assert m.data(m.index(0, 2), Qt.ItemDataRole.ToolTipRole) == dt.strftime(_DT_FMT)
    assert m.data(m.index(0, 3), Qt.ItemDataRole.ToolTipRole) == "alice"
    assert m.data(m.index(0, 4), Qt.ItemDataRole.ToolTipRole) == "fix bug"
    assert m.data(m.index(0, 5), Qt.ItemDataRole.ToolTipRole) == "/main"


def test_changeset_model_short_date_display():
    from biome_fm.plastic._components import ChangesetModel
    from biome_fm.plastic._models import Changeset
    from PySide6.QtCore import Qt
    dt = datetime(2026, 1, 25, 14, 32)
    m = ChangesetModel()
    m.reset([Changeset(1, dt, "alice", "/main", "msg")])
    display = m.data(m.index(0, 2), Qt.ItemDataRole.DisplayRole)
    assert display == "Jan 25, 14:32"


# ── CSDetailWidget — placeholder states ──────────────────────────────────────

def test_cs_detail_default_is_placeholder(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    w = CSDetailWidget()
    assert w._stack.currentIndex() == 0


def test_cs_detail_load_cs_shows_content(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import Changeset
    w = CSDetailWidget()
    w.load_cs(Changeset(1, datetime(2026, 1, 1), "x", "/m", "c"))
    assert w._stack.currentIndex() == 1


def test_cs_detail_clear_returns_to_placeholder(qapp):
    from biome_fm.plastic._components import CSDetailWidget
    from biome_fm.plastic._models import Changeset
    w = CSDetailWidget()
    w.load_cs(Changeset(1, datetime(2026, 1, 1), "x", "/m", "c"))
    w.clear()
    assert w._stack.currentIndex() == 0


# ── PlasticWindow queue/drain for cs_files ────────────────────────────────────

def test_set_cs_files_drains_to_detail(qapp):
    from biome_fm.plastic._window import PlasticWindow
    from biome_fm.plastic._models import CSDiffFile
    w = PlasticWindow()
    files = [CSDiffFile("/a.py", "M", 2, 1, "diff text")]
    w.set_cs_files(files)
    w._drain()
    assert w._cs_detail._file_model.rowCount() == 1
