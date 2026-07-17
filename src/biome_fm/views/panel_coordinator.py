from __future__ import annotations

from biome_fm.panel_manager import Effect, PanelManager, PanelState
from biome_fm.qt import (
    QDialog,
    QObject,
    QSplitter,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)


class PanelCoordinator(QObject):
    state_changed = Signal(str, str)  # (panel_name, "hidden"|"overlay"|"floating")

    def __init__(
        self,
        manager: PanelManager,
        panels: dict[str, QWidget],
        left_side: QWidget,
        right_side: QWidget,
        splitter: QSplitter,
        main_window: QWidget,
    ) -> None:
        super().__init__(main_window)
        self._mgr = manager
        self._panels = panels
        self._left = left_side
        self._right = right_side
        self._splitter = splitter
        self._main = main_window
        self._float: dict[str, QDialog] = {}
        self._in_splitter: dict[str, bool] = {n: True for n in panels}
        self._saved_sizes: dict[QWidget, int] | None = None
        self._hidden_widget: QWidget | None = None
        self._overlay_side: str = "right"  # "left" or "right" — which side the overlay occupies

    def toggle(self, name: str, active_side: str = "left") -> None:
        self._overlay_side = "right" if active_side == "left" else "left"
        self._apply(self._mgr.toggle(name))

    def detach(self, name: str) -> None:
        self._apply(self._mgr.detach(name))

    def reattach(self, name: str, active_side: str = "left") -> None:
        self._overlay_side = "right" if active_side == "left" else "left"
        self._apply(self._mgr.reattach(name))

    def _apply(self, effects: list[Effect]) -> None:
        # Capture sizes BEFORE any panel.show() corrupts splitter layout
        if self._saved_sizes is None and any(
            e.kind == "set_opposite_visible" and not e.value for e in effects
        ):
            raw = self._splitter.sizes()
            self._saved_sizes = {
                self._splitter.widget(i): raw[i] for i in range(len(raw))
            }
        for e in effects:
            match e.kind:
                case "show_overlay":
                    self._show_overlay(e.panel)
                case "show_floating":
                    self._show_floating(e.panel)
                case "hide":
                    self._hide_panel(e.panel)
                case "focus_floating":
                    self._focus_floating(e.panel)
                case "set_opposite_visible":
                    self._set_opposite_visible(e.value)
        for name in self._panels:
            self.state_changed.emit(name, self._mgr.state(name).value)

    def _set_opposite_visible(self, visible: bool) -> None:
        if not visible:
            new_hidden = self._left if self._overlay_side == "left" else self._right
            if self._hidden_widget is not None and self._hidden_widget is not new_hidden:
                self._hidden_widget.show()
            self._hidden_widget = new_hidden
            self._hidden_widget.hide()
            if self._saved_sizes:
                hidden_w = self._saved_sizes.get(self._hidden_widget, 0)
                sizes = []
                for i in range(self._splitter.count()):
                    w = self._splitter.widget(i)
                    if w is self._hidden_widget:
                        sizes.append(0)
                    elif w in self._panels.values() and w.isVisible():
                        sizes.append(hidden_w)
                    else:
                        sizes.append(self._saved_sizes.get(w, 0))
                self._splitter.setSizes(sizes)
        else:
            if self._hidden_widget is not None:
                self._hidden_widget.show()
                self._hidden_widget = None
            if self._saved_sizes:
                sizes = [
                    self._saved_sizes.get(self._splitter.widget(i), 0)
                    for i in range(self._splitter.count())
                ]
                self._splitter.setSizes(sizes)
                self._saved_sizes = None

    def _show_overlay(self, name: str) -> None:
        panel = self._panels[name]
        anim = getattr(panel, '_anim', None)
        if anim is not None and hasattr(anim, 'stop'):
            anim.stop()
        target = 0 if self._overlay_side == "left" else self._overlay_index(name)
        if not self._in_splitter[name]:
            self._splitter.insertWidget(target, panel)
            self._in_splitter[name] = True
        elif self._splitter.indexOf(panel) != target:
            self._splitter.insertWidget(target, panel)
        panel.setMaximumWidth(16777215)
        panel.show()

    def _show_floating(self, name: str) -> None:
        panel = self._panels[name]
        anim = getattr(panel, '_anim', None)
        if anim is not None and hasattr(anim, 'stop'):
            anim.stop()
        if self._in_splitter[name]:
            panel.hide()
            panel.setParent(None)
            self._in_splitter[name] = False
        panel.setMaximumWidth(16777215)
        panel.setMinimumWidth(0)
        dlg = QDialog(self._main)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.setWindowTitle(f"Biome FM — {name.title()}")
        dlg.resize(600, 800)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(panel)
        panel.show()
        dlg.finished.connect(lambda _result, _name=name: self._on_float_closed(_name))
        self._float[name] = dlg
        dlg.show()

    def _hide_panel(self, name: str) -> None:
        panel = self._panels[name]
        if name in self._float:
            dlg = self._float.pop(name)
            dlg.finished.disconnect()
            dlg.close()
        if not self._in_splitter[name]:
            self._splitter.insertWidget(self._overlay_index(name), panel)
            self._in_splitter[name] = True
        elif self._overlay_side == "left" and self._splitter.indexOf(panel) < 2:
            # Panel was moved to index 0 for left overlay — move it back to home
            self._splitter.insertWidget(self._overlay_index(name), panel)
        panel.hide()

    def _focus_floating(self, name: str) -> None:
        if name in self._float:
            self._float[name].raise_()
            self._float[name].activateWindow()

    def _on_float_closed(self, name: str) -> None:
        self._float.pop(name, None)
        # Re-insert panel into splitter before hiding
        panel = self._panels[name]
        if not self._in_splitter[name]:
            self._splitter.insertWidget(self._overlay_index(name), panel)
            self._in_splitter[name] = True
        self._apply(self._mgr.on_float_closed(name))

    def _overlay_index(self, name: str) -> int:
        base = {"preview": 2, "ai": 3, "search": 4, "terminal": 5}[name]
        if name in ("ai", "search", "terminal") and not self._in_splitter.get("preview", True):
            base -= 1
        if name in ("search", "terminal") and not self._in_splitter.get("ai", True):
            base -= 1
        if name == "terminal" and not self._in_splitter.get("search", True):
            base -= 1
        return min(base, self._splitter.count())

    def pane_sizes(self) -> list[int]:
        """Return logical pane sizes — reads _saved_sizes when overlay is active."""
        raw = self._splitter.sizes()
        if self._saved_sizes:
            return [
                self._saved_sizes.get(self._left, raw[0]),
                self._saved_sizes.get(self._right, raw[1]),
            ]
        return raw[:2]

    def save_state(self) -> dict[str, dict]:
        result = {}
        for name in self._panels:
            geo = ""
            if name in self._float:
                g = self._float[name].geometry()
                geo = f"{g.x()},{g.y()},{g.width()},{g.height()}"
            result[name] = {
                "state": self._mgr.state(name).value,
                "float_geometry": geo,
                "overlay_side": (
                    self._overlay_side if self._mgr.state(name) == PanelState.OVERLAY else "right"
                ),
            }
        return result

    def restore_state(self, data: dict[str, dict]) -> None:
        for name, d in data.items():
            if name not in self._panels:
                continue
            s = d.get("state", "hidden")
            if s == "overlay":
                self._overlay_side = d.get("overlay_side", "right")
                self._apply(self._mgr.set_state(name, PanelState.OVERLAY))
            elif s == "floating":
                self._apply(self._mgr.set_state(name, PanelState.FLOATING))
                geo = d.get("float_geometry", "")
                if geo and name in self._float:
                    try:
                        x, y, w, h = map(int, geo.split(","))
                        self._float[name].setGeometry(x, y, w, h)
                    except ValueError:
                        pass
