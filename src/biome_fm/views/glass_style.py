"""QProxyStyle that suppresses Fusion's opaque background fills for glass-tagged widgets."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QMenu,
    QProxyStyle,
    QSplitterHandle,
    QStyle,
    QWidget,
)

_GLASS_PROP = "_glass"
_FILTER_PROP = "_glass_filter"

_SKIP_CONTROLS = frozenset({
    QStyle.ControlElement.CE_MenuBarEmptyArea,
    QStyle.ControlElement.CE_ShapedFrame,
    QStyle.ControlElement.CE_HeaderEmptyArea,
})

_SKIP_PRIMITIVES = frozenset({
    QStyle.PrimitiveElement.PE_Widget,
    QStyle.PrimitiveElement.PE_Frame,
    QStyle.PrimitiveElement.PE_PanelScrollAreaCorner,
    QStyle.PrimitiveElement.PE_FrameTabBarBase,
})


class _GlassClearFilter(QObject):
    """Clears backing store before paint to prevent ghost pixels on translucent widgets."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Paint:
            p = QPainter(obj)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(obj.rect(), Qt.GlobalColor.transparent)
            p.end()
        return False


def mark_glass(widget: QWidget, *, recursive: bool = False) -> None:
    """Tag a widget so GlassStyle skips its opaque background fill."""
    widget.setProperty(_GLASS_PROP, True)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAutoFillBackground(False)
    if isinstance(widget, QAbstractScrollArea):
        vp = widget.viewport()
        vp.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        vp.setAutoFillBackground(False)
        if not vp.property(_FILTER_PROP):
            f = _GlassClearFilter(vp)
            vp.installEventFilter(f)
            vp.setProperty(_FILTER_PROP, True)
    else:
        if not widget.property(_FILTER_PROP):
            f = _GlassClearFilter(widget)
            widget.installEventFilter(f)
            widget.setProperty(_FILTER_PROP, True)
    if recursive:
        for child in widget.findChildren(QWidget):
            if isinstance(child, (QMenu, QSplitterHandle)):
                continue
            mark_glass(child)


def unmark_glass(widget: QWidget, *, recursive: bool = False) -> None:
    """Remove glass tags, restore opaque painting."""
    widget.setProperty(_GLASS_PROP, False)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    widget.setAutoFillBackground(True)
    if isinstance(widget, QAbstractScrollArea):
        vp = widget.viewport()
        vp.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        vp.setAutoFillBackground(True)
        for child in vp.children():
            if isinstance(child, _GlassClearFilter):
                vp.removeEventFilter(child)
                child.deleteLater()
        vp.setProperty(_FILTER_PROP, False)
    else:
        for child in widget.children():
            if isinstance(child, _GlassClearFilter):
                widget.removeEventFilter(child)
                child.deleteLater()
        widget.setProperty(_FILTER_PROP, False)
    if recursive:
        for child in widget.findChildren(QWidget):
            if isinstance(child, (QMenu, QSplitterHandle)):
                continue
            unmark_glass(child)


class GlassStyle(QProxyStyle):
    def __init__(self):
        super().__init__("fusion")

    def drawControl(self, element, option, painter, widget=None):
        if widget and widget.property(_GLASS_PROP) and element in _SKIP_CONTROLS:
            return
        super().drawControl(element, option, painter, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        if widget and widget.property(_GLASS_PROP) and element in _SKIP_PRIMITIVES:
            return
        super().drawPrimitive(element, option, painter, widget)
