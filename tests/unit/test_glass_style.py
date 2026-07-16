"""Unit tests for GlassStyle, mark_glass, unmark_glass."""
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from biome_fm.views.glass_style import (
    GlassStyle,
    _FILTER_PROP,
    _GLASS_PROP,
    _GlassClearFilter,
    _SKIP_CONTROLS,
    _SKIP_PRIMITIVES,
    mark_glass,
    unmark_glass,
)


def test_mark_glass_sets_properties(qtbot):
    w = QWidget()
    qtbot.addWidget(w)
    mark_glass(w)
    assert w.property(_GLASS_PROP) is True
    assert w.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert w.autoFillBackground() is False


def test_unmark_glass_clears_properties(qtbot):
    w = QWidget()
    qtbot.addWidget(w)
    mark_glass(w)
    unmark_glass(w)
    assert w.property(_GLASS_PROP) is False
    assert not w.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert w.autoFillBackground() is True


def test_mark_glass_recursive(qtbot):
    parent = QWidget()
    child = QWidget(parent)
    qtbot.addWidget(parent)
    mark_glass(parent, recursive=True)
    assert child.property(_GLASS_PROP) is True


def test_unmark_glass_recursive(qtbot):
    parent = QWidget()
    child = QWidget(parent)
    qtbot.addWidget(parent)
    mark_glass(parent, recursive=True)
    unmark_glass(parent, recursive=True)
    assert child.property(_GLASS_PROP) is False
    assert child.autoFillBackground() is True


def test_glass_style_skips_tagged_control():
    style = GlassStyle()
    widget = MagicMock()
    widget.property.return_value = True
    painter = MagicMock()
    option = MagicMock()
    for ce in _SKIP_CONTROLS:
        painter.reset_mock()
        style.drawControl(ce, option, painter, widget)


def test_glass_style_skips_tagged_primitive():
    style = GlassStyle()
    widget = MagicMock()
    widget.property.return_value = True
    painter = MagicMock()
    option = MagicMock()
    for pe in _SKIP_PRIMITIVES:
        style.drawPrimitive(pe, option, painter, widget)


def test_label_gets_clear_filter(qtbot):
    from PySide6.QtWidgets import QLabel
    lbl = QLabel("test")
    qtbot.addWidget(lbl)
    mark_glass(lbl)
    assert lbl.property(_FILTER_PROP) is True
    has_filter = any(isinstance(c, _GlassClearFilter) for c in lbl.children())
    assert has_filter


def test_non_scroll_area_filter_removed_on_unmark(qtbot):
    from PySide6.QtWidgets import QLabel
    lbl = QLabel("test")
    qtbot.addWidget(lbl)
    mark_glass(lbl)
    unmark_glass(lbl)
    assert lbl.property(_FILTER_PROP) is False


def test_recursive_skips_splitter_handle(qtbot):
    from PySide6.QtWidgets import QSplitter
    sp = QSplitter()
    qtbot.addWidget(sp)
    left = QWidget(sp)
    right = QWidget(sp)
    sp.addWidget(left)
    sp.addWidget(right)
    mark_glass(sp, recursive=True)
    handle = sp.handle(1)
    assert handle is not None
    assert not handle.property(_GLASS_PROP)


def test_recursive_skips_qmenu(qtbot):
    from PySide6.QtWidgets import QMenu
    parent = QWidget()
    qtbot.addWidget(parent)
    menu = QMenu(parent)
    mark_glass(parent, recursive=True)
    assert not menu.property(_GLASS_PROP)


def test_prepare_glass_exception_returns_false():
    from biome_fm.views import glass
    window = MagicMock()
    with patch.object(glass, "_glass") as mock_lib:
        mock_lib.prepare_window_for_glass.side_effect = RuntimeError("boom")
        result = glass.prepare_glass(window)
    assert result is False
