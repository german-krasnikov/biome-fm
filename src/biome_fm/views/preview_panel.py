"""PreviewPanel — passive sidebar panel. Implements PreviewViewProtocol."""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from biome_fm.preview.provider import ContentKind, PreviewMode, PreviewResult
from biome_fm.views._zoomable_image import ZoomableImageWidget


class PreviewPanel(QWidget):
    _DEFAULT_WIDTH = 350
    visibility_changed = Signal(bool)
    detach_requested = Signal()
    close_requested = Signal()
    mode_changed = Signal(object)  # emits PreviewMode
    summarize_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Preview panel")
        self.setMinimumWidth(0)
        self._anim: QPropertyAnimation | None = None
        self._reduce_motion: bool = False

        self._stack = QStackedWidget()
        self._busy_label = QLabel("Loading…", alignment=Qt.AlignmentFlag.AlignCenter)
        self._img_widget = ZoomableImageWidget()
        self._text_view = QTextBrowser()
        self._text_view.setReadOnly(True)
        self._text_view.setOpenExternalLinks(True)
        self._dark = True
        self._code_alpha = 140

        for w in (self._busy_label, self._img_widget, self._text_view):
            self._stack.addWidget(w)
        self._stack.setCurrentWidget(self._busy_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2)
        header.addWidget(QLabel("Preview"))
        _ai_btn = QPushButton("AI ✨")
        _ai_btn.setFixedHeight(20)
        _ai_btn.setToolTip("Summarize file with AI")
        _ai_btn.clicked.connect(lambda: self.summarize_requested.emit())
        header.addWidget(_ai_btn)
        header.addStretch()
        from biome_fm.views._panel_buttons import add_panel_buttons
        add_panel_buttons(header, self.detach_requested, self.close_requested)
        layout.addLayout(header)

        mode_bar = QHBoxLayout()
        mode_bar.setContentsMargins(0, 0, 0, 0)
        mode_bar.setSpacing(2)
        for label, mode in [
            ("Auto", PreviewMode.AUTO),
            ("Text", PreviewMode.TEXT),
            ("Hex", PreviewMode.HEX),
            ("Raw", PreviewMode.RAW),
            ("Log", PreviewMode.GIT_LOG),
            ("Blame", PreviewMode.GIT_BLAME),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(20)
            btn.clicked.connect(lambda _checked=False, m=mode: self.mode_changed.emit(m))
            mode_bar.addWidget(btn)
        mode_bar.addStretch()
        layout.addLayout(mode_bar)

        # Find bar
        self._find_bar = QWidget()
        find_row = QHBoxLayout(self._find_bar)
        find_row.setContentsMargins(0, 0, 0, 0)
        find_row.setSpacing(4)
        find_row.addWidget(QLabel("Find:"))
        self._find_edit = QLineEdit()
        self._find_edit.installEventFilter(self)
        self._find_edit.textChanged.connect(self._find_current)
        self._find_edit.returnPressed.connect(self._find_next)
        find_row.addWidget(self._find_edit)
        self._find_label = QLabel("")
        find_row.addWidget(self._find_label)
        self._find_bar.hide()
        layout.addWidget(self._find_bar)

        layout.addWidget(self._stack)

    # ── PreviewViewProtocol ──────────────────────────────────────────────

    def show_result(self, result: PreviewResult) -> None:
        self._find_label.setText("")
        match result.kind:
            case ContentKind.IMAGE:
                px = QPixmap()
                px.loadFromData(result.data)  # type: ignore[arg-type]
                self._img_widget.set_pixmap(px)
                self._stack.setCurrentWidget(self._img_widget)
            case ContentKind.HTML:
                self._text_view.setHtml(result.data)  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case ContentKind.TEXT:
                self._text_view.setPlainText(result.data)  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case ContentKind.MARKDOWN:
                from biome_fm.preview.markdown_renderer import render as _md_render
                self._text_view.setHtml(_md_render(result.data, self._dark, self._code_alpha))  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case _:  # ERROR
                self._text_view.setPlainText(f"Error: {result.data}")
                self._stack.setCurrentWidget(self._text_view)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark

    def set_code_alpha(self, alpha: int) -> None:
        self._code_alpha = alpha

    def set_busy(self, busy: bool) -> None:
        if busy:
            self._stack.setCurrentWidget(self._busy_label)

    def set_reduce_motion(self, val: bool) -> None:
        self._reduce_motion = val

    def _os_reduce_motion(self) -> bool:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            return bool(app and not app.styleHints().animationsEnabled())
        except AttributeError:
            return False

    def set_visible(self, visible: bool) -> None:
        if self._reduce_motion or self._os_reduce_motion():
            self.setVisible(visible)
            return
        if self._anim is not None and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        if visible:
            self.show()
            self.setMaximumWidth(16777215)  # reset before open animation
            self._anim = self._animate(0, self._DEFAULT_WIDTH)
        else:
            self._anim = self._animate(self.width(), 0)
            self._anim.finished.connect(self.hide)

    def is_panel_visible(self) -> bool:
        return self.isVisible()

    # ── Qt events → signal ───────────────────────────────────────────────

    def showEvent(self, event: object) -> None:
        super().showEvent(event)  # type: ignore[arg-type]
        self.visibility_changed.emit(True)

    def hideEvent(self, event: object) -> None:
        super().hideEvent(event)  # type: ignore[arg-type]
        self.visibility_changed.emit(False)

    # ── Find bar ────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._show_find_bar()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj: object, event: object) -> bool:
        if obj is self._find_edit and isinstance(event, QEvent):
            if event.type() == QEvent.Type.KeyPress:
                assert isinstance(event, QKeyEvent)
                if event.key() == Qt.Key.Key_Escape:
                    self._find_bar.hide()
                    return True
        return super().eventFilter(obj, event)  # type: ignore[arg-type]

    def _show_find_bar(self) -> None:
        self._find_bar.show()
        self._find_edit.setFocus()
        self._find_edit.selectAll()

    def _find_current(self, text: str) -> None:
        if not text:
            self._find_label.setText("")
            return
        # Reset cursor to start, then search forward
        cursor = self._text_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self._text_view.setTextCursor(cursor)
        found = self._text_view.find(text)
        self._find_label.setText("Found" if found else "Not found")

    def _find_next(self) -> bool:
        text = self._find_edit.text()
        if not text:
            return False
        found = self._text_view.find(text)
        if not found:
            cursor = self._text_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._text_view.setTextCursor(cursor)
            found = self._text_view.find(text)
        self._find_label.setText("Found" if found else "Not found")
        return found

    def _find_prev(self) -> bool:
        from PySide6.QtGui import QTextDocument
        text = self._find_edit.text()
        if not text:
            return False
        found = self._text_view.find(text, QTextDocument.FindFlag.FindBackward)
        if not found:
            cursor = self._text_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self._text_view.setTextCursor(cursor)
            found = self._text_view.find(text, QTextDocument.FindFlag.FindBackward)
        self._find_label.setText("Found" if found else "Not found")
        return found

    # ── Animation ────────────────────────────────────────────────────────

    def _animate(self, start: int, end: int) -> QPropertyAnimation:
        anim = QPropertyAnimation(self, b"maximumWidth", self)
        anim.setDuration(150)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        return anim
