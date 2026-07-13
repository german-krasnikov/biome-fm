"""SearchDialog — modal dialog for file search parameters."""
from __future__ import annotations

from pathlib import Path

from biome_fm.presenters.search_presenter import SearchMode
from biome_fm.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SearchDialog(QDialog):
    """Modal dialog returning search parameters."""

    def __init__(self, root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find Files")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Search in: {root}"))

        form = QFormLayout()

        self._query = QLineEdit()
        self._query.setPlaceholderText("*.txt, foo*.py, ...")
        form.addRow("Pattern:", self._query)

        self._mode = QComboBox()
        self._mode.addItem("Wildcard", SearchMode.NAME_WILDCARD)
        self._mode.addItem("Regex", SearchMode.NAME_REGEX)
        self._mode.addItem("Content", SearchMode.CONTENT)
        form.addRow("Mode:", self._mode)

        self._max_results = QSpinBox()
        self._max_results.setRange(10, 100_000)
        self._max_results.setValue(1000)
        self._max_results.setSingleStep(100)
        form.addRow("Max results:", self._max_results)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._query.setFocus()

    def _on_accept(self) -> None:
        if self._query.text().strip():
            self.accept()

    @property
    def query(self) -> str:
        return self._query.text().strip()

    @property
    def mode(self) -> SearchMode:
        return self._mode.currentData()

    @property
    def max_results(self) -> int:
        return self._max_results.value()

    @staticmethod
    def get_params(
        root: Path, parent: QWidget | None = None
    ) -> tuple[str, SearchMode, int] | None:
        """Show dialog, return (query, mode, max_results) or None if cancelled."""
        dlg = SearchDialog(root, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.query, dlg.mode, dlg.max_results
        return None
