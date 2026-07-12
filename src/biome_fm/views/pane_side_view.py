"""PaneSideView — tabbed pane container."""
from __future__ import annotations

from pathlib import Path as _P

from biome_fm.qt import (
    QApplication,
    QStackedWidget,
    QTableView,
    Qt,
    QTabBar,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views.pane_view import PaneView


class _PathTabBar(QTabBar):
    """Middle-click or Ctrl+click copies full path from tab tooltip."""

    def mousePressEvent(self, event: object) -> None:
        btn = event.button()  # type: ignore[attr-defined]
        mods = event.modifiers()  # type: ignore[attr-defined]
        if btn == Qt.MouseButton.MiddleButton or (
            btn == Qt.MouseButton.LeftButton
            and mods & Qt.KeyboardModifier.ControlModifier
        ):
            idx = self.tabAt(event.pos())  # type: ignore[attr-defined]
            if idx >= 0:
                QApplication.clipboard().setText(self.tabToolTip(idx))
                return
        super().mousePressEvent(event)  # type: ignore[arg-type]


class PaneSideView(QWidget):
    """Tabbed container for multiple PaneView instances."""

    tab_close_requested = Signal(int)
    tab_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._tab_bar = _PathTabBar()
        self._tab_bar.setTabsClosable(False)
        self._tab_bar.setMovable(True)
        self._stack = QStackedWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 1, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._stack)

        self._tab_bar.tabCloseRequested.connect(self.tab_close_requested)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self.tab_changed.emit(idx)

    # ── TabsViewProtocol ─────────────────────────────────────────

    def _sync_closable(self) -> None:
        self._tab_bar.setTabsClosable(self._tab_bar.count() > 1)

    def add_tab(self, title: str) -> int:
        idx = self._tab_bar.addTab(title)
        self._sync_closable()
        return idx

    def remove_tab(self, idx: int) -> None:
        w = self._stack.widget(idx)
        if w is not None:
            self._stack.removeWidget(w)
        self._tab_bar.removeTab(idx)
        self._sync_closable()

    def set_active_tab(self, idx: int) -> None:
        self._tab_bar.blockSignals(True)
        self._tab_bar.setCurrentIndex(idx)
        self._tab_bar.blockSignals(False)
        self._stack.setCurrentIndex(idx)

    def set_tab_title(self, idx: int, title: str) -> None:
        self._tab_bar.setTabToolTip(idx, title)
        p = _P(title)
        home = _P.home()
        try:
            display = "~/" + str(p.relative_to(home))
        except ValueError:
            display = p.name or title
        if len(display) > 30:
            display = "…/" + p.name
        self._tab_bar.setTabText(idx, display)

    def set_tab_tooltip(self, idx: int, tooltip: str) -> None:
        self._tab_bar.setTabToolTip(idx, tooltip)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        s = self.style()
        s.unpolish(self)
        s.polish(self)
        self.update()
        for tv in self.findChildren(QTableView):
            s.unpolish(tv)
            s.polish(tv)

    # ── Factory ──────────────────────────────────────────────────

    def new_pane(self) -> PaneView:
        """Create a new PaneView and add to stack."""
        pane = PaneView()
        self._stack.addWidget(pane)
        return pane
