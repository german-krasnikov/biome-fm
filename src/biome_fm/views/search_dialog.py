"""SearchDialog — modal dialog for file search parameters."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from biome_fm.presenters.search_presenter import SearchMode
from biome_fm.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from biome_fm.models.search_template_store import SearchTemplate, SearchTemplateStore


class SearchDialog(QDialog):
    """Modal dialog returning search parameters."""

    def __init__(
        self,
        root: Path,
        parent: QWidget | None = None,
        *,
        store: SearchTemplateStore | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find Files")
        self.setMinimumWidth(400)
        self._store = store

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Search in: {root}"))

        if store is not None:
            self._tmpl_combo = QComboBox()
            self._tmpl_combo.addItem("-- no template --")
            for t in store.templates:
                self._tmpl_combo.addItem(t.name)
            self._tmpl_combo.currentIndexChanged.connect(self._load_template)

            btn_save = QPushButton("Save")
            btn_save.clicked.connect(self._save_template)
            btn_del = QPushButton("Delete")
            btn_del.clicked.connect(self._delete_template)

            row = QHBoxLayout()
            row.addWidget(self._tmpl_combo, 1)
            row.addWidget(btn_save)
            row.addWidget(btn_del)
            layout.addLayout(row)

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

    # ── Template helpers (only called when store is set) ─────────────────────

    def _load_template(self, idx: int) -> None:
        if idx == 0 or self._store is None:
            return
        templates = self._store.templates
        t = templates[idx - 1]  # idx 0 = "-- no template --"
        self._query.setText(t.pattern)
        mode_map = {
            "wildcard": SearchMode.NAME_WILDCARD,
            "regex": SearchMode.NAME_REGEX,
            "content": SearchMode.CONTENT,
        }
        mode_idx = self._mode.findData(mode_map.get(t.mode, SearchMode.NAME_WILDCARD))
        if mode_idx >= 0:
            self._mode.setCurrentIndex(mode_idx)
        self._max_results.setValue(t.max_results)

    def _save_template(self) -> None:
        if self._store is None:
            return
        from biome_fm.models.search_template_store import SearchTemplate
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not name.strip():
            return
        mode_str = {
            SearchMode.NAME_WILDCARD: "wildcard",
            SearchMode.NAME_REGEX: "regex",
            SearchMode.CONTENT: "content",
        }.get(self._mode.currentData(), "wildcard")
        t = SearchTemplate(name=name.strip(), pattern=self._query.text().strip(),
                           mode=mode_str, max_results=self._max_results.value())
        self._store.save(t)
        # Refresh combo without triggering _load_template
        self._tmpl_combo.blockSignals(True)
        self._tmpl_combo.clear()
        self._tmpl_combo.addItem("-- no template --")
        for tmpl in self._store.templates:
            self._tmpl_combo.addItem(tmpl.name)
        self._tmpl_combo.blockSignals(False)

    def _delete_template(self) -> None:
        if self._store is None:
            return
        idx = self._tmpl_combo.currentIndex()
        if idx == 0:
            return
        name = self._tmpl_combo.currentText()
        self._store.delete(name)
        self._tmpl_combo.removeItem(idx)

    # ── Public interface ──────────────────────────────────────────────────────

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
        root: Path,
        parent: QWidget | None = None,
        *,
        store: SearchTemplateStore | None = None,
    ) -> tuple[str, SearchMode, int] | None:
        """Show dialog, return (query, mode, max_results) or None if cancelled."""
        dlg = SearchDialog(root, parent, store=store)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.query, dlg.mode, dlg.max_results
        return None
