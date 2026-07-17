"""BreadcrumbBar — path bar with clickable segments + edit mode."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.qt import (
    QApplication,
    QComboBox,
    QDrag,
    QEvent,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSize,
    QSizePolicy,
    QStackedWidget,
    Qt,
    QTimer,
    QToolButton,
    QWidget,
    Signal,
)
from biome_fm.utils.opener import open_file
from biome_fm.utils.platform import IS_MAC, open_terminal, reveal_in_finder
from biome_fm.views.dnd_utils import _MIME, make_path_mime

_MOVE_MODS = Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.AltModifier

# ---------------------------------------------------------------------------
# Pure helper — no Qt
# ---------------------------------------------------------------------------

def path_segments(path: Path) -> list[tuple[str, Path]]:
    """Split path into (label, full_path) pairs, root → leaf."""
    parts = path.parts
    result = []
    for i, part in enumerate(parts):
        full = Path(*parts[: i + 1]) if i > 0 else Path(parts[0])
        result.append((part, full))
    return result


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class _PathComboBox(QComboBox):
    path_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMaxVisibleItems(30)
        self.lineEdit().setPlaceholderText("Path...")
        self.lineEdit().returnPressed.connect(self._emit)
        self.activated.connect(lambda _i: self._emit())
        from PySide6.QtCore import QDir
        from PySide6.QtWidgets import QCompleter, QFileSystemModel
        fs_model = QFileSystemModel(self)
        fs_model.setRootPath("")
        fs_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        completer = QCompleter(fs_model, self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setMaxVisibleItems(10)
        self.lineEdit().setCompleter(completer)

    def _emit(self):
        text = self.lineEdit().text().strip()
        if text:
            self.path_entered.emit(text)


class _SegmentButton(QToolButton):
    navigated = Signal(object)       # Path
    files_dropped = Signal(list, bool, object)  # [Path], move, dest Path

    def __init__(self, label: str, full_path: Path, active: bool = False, parent=None):
        super().__init__(parent)
        self._path = full_path
        self._drag_start = None
        self.setText(label)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("QToolButton { padding: 0 2px; margin: 0; }")
        self.setProperty("crumb", True)
        self.setProperty("crumb_active", active)
        self.clicked.connect(self._emit_navigated)
        self.setAcceptDrops(True)

    def _emit_navigated(self) -> None:
        self.navigated.emit(self._path)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._drag_start is not None
                and (event.pos() - self._drag_start).manhattanLength()
                >= QApplication.startDragDistance()):
            drag = QDrag(self)
            drag.setMimeData(make_path_mime([str(self._path)]))
            self._drag_start = None
            drag.exec(Qt.DropAction.CopyAction)
            return
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(_MIME):
            raw = mime.data(_MIME).data().decode()
            paths = [Path(p) for p in raw.splitlines() if p]
            move = bool(event.modifiers() & _MOVE_MODS)
            self.files_dropped.emit(paths, move, self._path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self.window())
        menu.addAction("Copy Path", lambda: QApplication.clipboard().setText(str(self._path)))
        menu.addAction(
            "Copy Name",
            lambda: QApplication.clipboard().setText(self._path.name or str(self._path)),
        )
        if IS_MAC:
            menu.addAction("Show in Finder", lambda: reveal_in_finder(self._path))
        else:
            menu.addAction("Open in File Manager", lambda: open_file(self._path))
        menu.addAction("Open Terminal Here", lambda: open_terminal(self._path))
        parent = self._path.parent
        if parent != self._path:  # skip root
            try:
                siblings = sorted(
                    (e.name for e in os.scandir(parent) if e.is_dir()),
                    key=str.lower,
                )
            except OSError:
                siblings = []
            if siblings:
                menu.addSeparator()
                sub = menu.addMenu("Siblings")
                for name in siblings:
                    sib = parent / name
                    label = f"▶ {name}" if sib == self._path else name
                    sub.addAction(label, lambda p=sib: self.navigated.emit(p))
        menu.popup(event.globalPos())


class _CrumbRow(QWidget):
    segment_clicked = Signal(object)  # Path
    edit_requested = Signal()
    files_dropped = Signal(list, bool, object)  # [Path], move, dest Path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def set_path(self, path: Path) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        segments = path_segments(path)
        for i, (label, full_path) in enumerate(segments):
            btn = _SegmentButton(label, full_path, active=(full_path == path), parent=self)
            btn.navigated.connect(self.segment_clicked)
            btn.files_dropped.connect(self.files_dropped)
            self._layout.addWidget(btn)
            if i < len(segments) - 1:
                sep = QLabel("›", parent=self)  # noqa: RUF001
                sep.setObjectName("crumb_sep")
                sep.setStyleSheet("padding: 0; margin: 0;")
                self._layout.addWidget(sep)
        QTimer.singleShot(0, self.adjustSize)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit()
        super().mousePressEvent(event)


class _CrumbScrollArea(QScrollArea):
    """Fixed-height horizontally-scrollable container for _CrumbRow."""
    BAR_H = 28

    def __init__(self, crumb_row, parent=None):
        super().__init__(parent)
        self.setWidget(crumb_row)
        self.setWidgetResizable(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedHeight(self.BAR_H)
        self.viewport().setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def minimumSizeHint(self) -> QSize:
        return QSize(50, self.BAR_H)

    def wheelEvent(self, event) -> None:
        dx = event.angleDelta().x()
        dy = event.angleDelta().y()
        if abs(dx) > abs(dy) and dx != 0:
            sb = self.horizontalScrollBar()
            sb.setValue(sb.value() - dx)
            event.accept()
        else:
            super().wheelEvent(event)


class BreadcrumbBar(QWidget):
    path_entered = Signal(str)
    files_dropped = Signal(list, bool, object)  # [Path], move, dest Path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("Path navigation")
        self._crumb = _CrumbRow()
        self._scroll = _CrumbScrollArea(self._crumb)

        self._left_arrow = QToolButton()
        self._left_arrow.setText("‹")  # noqa: RUF001
        self._left_arrow.setFixedWidth(18)
        self._left_arrow.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._left_arrow.hide()

        self._right_arrow = QToolButton()
        self._right_arrow.setText("›")  # noqa: RUF001
        self._right_arrow.setFixedWidth(18)
        self._right_arrow.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._right_arrow.hide()

        self._combo = _PathComboBox()
        self._stack = QStackedWidget()

        crumb_wrapper = QWidget()
        hl = QHBoxLayout(crumb_wrapper)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(2)
        hl.addWidget(self._left_arrow)
        hl.addWidget(self._scroll)
        hl.addWidget(self._right_arrow)

        self._stack.addWidget(crumb_wrapper)  # index 0
        self._stack.addWidget(self._combo)     # index 1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(36)

        sb = self._scroll.horizontalScrollBar()
        sb.valueChanged.connect(self._update_arrows)
        sb.rangeChanged.connect(self._update_arrows)
        self._left_arrow.clicked.connect(lambda: sb.setValue(sb.value() - 80))
        self._right_arrow.clicked.connect(lambda: sb.setValue(sb.value() + 80))

        self._crumb.segment_clicked.connect(lambda p: self.path_entered.emit(str(p)))
        self._crumb.edit_requested.connect(self.activate_edit)
        self._crumb.files_dropped.connect(self.files_dropped)
        self._combo.path_entered.connect(self._commit_edit)
        self._combo.lineEdit().installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        if obj is self._combo.lineEdit() and event.type() == QEvent.Type.FocusOut:
            self._dismiss_edit()
        return super().eventFilter(obj, event)

    def _update_arrows(self, *_) -> None:
        sb = self._scroll.horizontalScrollBar()
        self._left_arrow.setVisible(sb.value() > 0)
        self._right_arrow.setVisible(sb.value() < sb.maximum())

    def _scroll_to_end(self) -> None:
        sb = self._scroll.horizontalScrollBar()
        sb.setValue(sb.maximum())
        self._update_arrows()

    def set_path(self, path: Path) -> None:
        self._crumb.set_path(path)
        self._combo.lineEdit().setText(str(path))
        self._stack.setCurrentIndex(0)
        QTimer.singleShot(0, lambda: QTimer.singleShot(0, self._scroll_to_end))

    def set_nav_history(self, paths: list[Path]) -> None:
        self._combo.blockSignals(True)
        current = self._combo.lineEdit().text()
        self._combo.clear()
        self._combo.addItems([str(p) for p in paths])
        self._combo.lineEdit().setText(current)
        self._combo.blockSignals(False)

    def show_error(self, message: str) -> None:
        self._combo.lineEdit().setText(f"Error: {message}")
        self._stack.setCurrentIndex(1)

    def activate_edit(self) -> None:
        self._stack.setCurrentIndex(1)
        self._combo.lineEdit().selectAll()
        self._combo.setFocus()

    def _commit_edit(self, text: str) -> None:
        self._stack.setCurrentIndex(0)
        self.path_entered.emit(text)

    def _dismiss_edit(self) -> None:
        self._stack.setCurrentIndex(0)

    # Compat shim so callers that still use lineEdit() keep working
    def lineEdit(self):
        return self._combo.lineEdit()
