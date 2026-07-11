"""PaneSideView — tabbed pane container."""
from __future__ import annotations

from biome_fm.qt import (
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views.pane_view import PaneView


class PaneSideView(QWidget):
    """Tabbed container for multiple PaneView instances."""

    tab_close_requested = Signal(int)
    tab_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tab_bar = QTabBar()
        self._tab_bar.setTabsClosable(True)
        self._tab_bar.setMovable(False)
        self._stack = QStackedWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._stack)

        self._tab_bar.tabCloseRequested.connect(self.tab_close_requested)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self.tab_changed.emit(idx)

    # ── TabsViewProtocol ─────────────────────────────────────────

    def add_tab(self, title: str) -> int:
        return self._tab_bar.addTab(title)

    def remove_tab(self, idx: int) -> None:
        w = self._stack.widget(idx)
        if w is not None:
            self._stack.removeWidget(w)
        self._tab_bar.removeTab(idx)

    def set_active_tab(self, idx: int) -> None:
        self._tab_bar.blockSignals(True)
        self._tab_bar.setCurrentIndex(idx)
        self._tab_bar.blockSignals(False)
        self._stack.setCurrentIndex(idx)

    def set_tab_title(self, idx: int, title: str) -> None:
        self._tab_bar.setTabText(idx, title)

    # ── Factory ──────────────────────────────────────────────────

    def new_pane(self) -> PaneView:
        """Create a new PaneView and add to stack."""
        pane = PaneView()
        self._stack.addWidget(pane)
        return pane
