"""Tag editor dialog — chip-style tag list with add/remove."""
from __future__ import annotations

from biome_fm.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)


class TagDialog(QDialog):
    def __init__(
        self,
        current_tags: list[str],
        all_tags: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tag Files")
        self._tags: list[str] = list(current_tags)

        layout = QVBoxLayout(self)

        # Chip area
        chip_widget = QWidget()
        self._chip_area = QHBoxLayout(chip_widget)
        self._chip_area.setContentsMargins(0, 0, 0, 0)
        self._chip_area.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(chip_widget)

        for t in self._tags:
            self._add_chip(t)

        # Quick-select from known tags
        self._combo = QComboBox()
        self._combo.addItems([t for t in all_tags if t not in self._tags])
        self._combo.setEditable(False)
        self._combo.setPlaceholderText("Select existing tag…")

        def _pick_from_combo():
            t = self._combo.currentText()
            if t and t not in self._tags:
                self._tags.append(t)
                self._add_chip(t)

        self._combo.activated.connect(lambda _: _pick_from_combo())
        layout.addWidget(self._combo)

        # New tag input
        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("New tag name…")
        self._btn_add = QPushButton("Add")
        self._btn_add.clicked.connect(self._on_add)
        self._input.returnPressed.connect(self._on_add)
        row.addWidget(self._input)
        row.addWidget(self._btn_add)
        layout.addLayout(row)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_chip(self, tag: str) -> None:
        chip = QPushButton(f"{tag} ×")
        chip.setFlat(True)
        chip.clicked.connect(lambda _, t=tag: self._remove_tag(t))
        self._chip_area.addWidget(chip)

    def _remove_tag(self, tag: str) -> None:
        self._tags = [t for t in self._tags if t != tag]
        # Rebuild chip area
        while self._chip_area.count():
            item = self._chip_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for t in self._tags:
            self._add_chip(t)

    def _on_add(self) -> None:
        tag = self._input.text().strip()
        if tag and tag not in self._tags:
            self._tags.append(tag)
            self._add_chip(tag)
            self._input.clear()

    def result_tags(self) -> list[str]:
        return list(self._tags)

    @staticmethod
    def get_tags(
        current_tags: list[str],
        all_tags: list[str],
        parent: QWidget | None = None,
    ) -> list[str] | None:
        dlg = TagDialog(current_tags, all_tags, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.result_tags()
        return None
