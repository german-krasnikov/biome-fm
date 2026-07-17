"""AI Context Actions dialog — shows AI-suggested actions for selected files."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class AIContextDialog(QDialog):
    """Show AI-suggested action labels for a list of files."""

    def __init__(self, items: list[str], provider: object, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Actions")
        layout = QVBoxLayout(self)

        if not getattr(provider, "available", False):
            layout.addWidget(QLabel("AI not configured"))
            btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            btn.rejected.connect(self.reject)
            layout.addWidget(btn)
            return

        layout.addWidget(QLabel(f"Suggested actions for: {', '.join(items)}"))
        layout.addWidget(QLabel("Loading…"))
        QApplication.processEvents()

        # Query AI
        prompt = f"For these files: {', '.join(items)}. Suggest 3-5 brief action labels (one per line)."
        try:
            text = provider.chat([{"role": "user", "content": prompt}])
        except Exception:
            text = ""

        # Remove Loading label, add results
        layout.itemAt(1).widget().deleteLater()

        self._list = QListWidget()
        for line in text.splitlines():
            line = line.strip().lstrip("0123456789.-) ")
            if line:
                self._list.addItem(line)
        layout.addWidget(self._list)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_selected)
        layout.addWidget(copy_btn)

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(self.reject)
        layout.addWidget(btn)

    def _copy_selected(self) -> None:
        item = self._list.currentItem()
        if item:
            QApplication.clipboard().setText(item.text())
