"""SearchDialog — modal dialog for file search parameters."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QGroupBox

from biome_fm.presenters.search_presenter import DEFAULT_EXCLUDE, SearchFilter, SearchMode, SearchScope
from biome_fm.qt import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStringListModel,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from biome_fm.models.search_template_store import SearchTemplateStore


class SearchDialog(QDialog):
    """Modal dialog returning search parameters."""

    def __init__(
        self,
        root: Path,
        parent: QWidget | None = None,
        *,
        store: SearchTemplateStore | None = None,
        history: list[str] | None = None,
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
        self._query.setAccessibleName("Search query")
        self._query.setPlaceholderText("*.txt, foo*.py, ...")
        if history:
            completer = QCompleter(QStringListModel(history, self._query), self._query)
            self._query.setCompleter(completer)
        form.addRow("Pattern:", self._query)

        self._mode = QComboBox()
        self._mode.addItem("Wildcard", SearchMode.NAME_WILDCARD)
        self._mode.addItem("Regex", SearchMode.NAME_REGEX)
        self._mode.addItem("Content", SearchMode.CONTENT)
        self._mode.addItem("Content (Regex)", SearchMode.CONTENT_REGEX)
        form.addRow("Mode:", self._mode)

        self._scope = QComboBox()
        self._scope.addItem("Subtree", SearchScope.SUBTREE)
        self._scope.addItem("Current dir only", SearchScope.CURRENT_DIR)
        self._scope.addItem("Selected files", SearchScope.SELECTED_FILES)
        self._scope.addItem("Both panes", SearchScope.BOTH_PANES)
        form.addRow("Scope:", self._scope)

        self._max_results = QSpinBox()
        self._max_results.setRange(10, 100_000)
        self._max_results.setValue(1000)
        self._max_results.setSingleStep(100)
        form.addRow("Max results:", self._max_results)

        self._exclude = QLineEdit()
        self._exclude.setPlaceholderText("comma-separated dir names / fnmatch patterns")
        self._exclude.setText(", ".join(DEFAULT_EXCLUDE))
        form.addRow("Exclude dirs:", self._exclude)

        self._case_sensitive = QCheckBox("Aa  Case sensitive")
        self._whole_word = QCheckBox("\\b  Whole word")
        flags_row = QHBoxLayout()
        flags_row.addWidget(self._case_sensitive)
        flags_row.addWidget(self._whole_word)
        flags_row.addStretch()
        form.addRow("Options:", flags_row)

        layout.addLayout(form)

        # Advanced filters (collapsible via checkbox)
        adv_box = QGroupBox("Advanced filters")
        adv_box.setCheckable(True)
        adv_box.setChecked(False)
        adv_form = QFormLayout(adv_box)

        self._min_size = QSpinBox()
        self._min_size.setRange(0, 10_000_000)
        self._min_size.setSuffix(" B")
        adv_form.addRow("Min size:", self._min_size)

        self._max_size = QSpinBox()
        self._max_size.setRange(0, 10_000_000)
        self._max_size.setSuffix(" B")
        adv_form.addRow("Max size:", self._max_size)

        self._mod_after = QDateEdit()
        self._mod_after.setCalendarPopup(True)
        self._mod_after.setSpecialValueText("(any)")
        self._mod_after.setDate(QDate(2000, 1, 1))
        adv_form.addRow("Modified after:", self._mod_after)

        self._mod_before = QDateEdit()
        self._mod_before.setCalendarPopup(True)
        self._mod_before.setSpecialValueText("(any)")
        self._mod_before.setDate(QDate(2099, 12, 31))
        adv_form.addRow("Modified before:", self._mod_before)

        self._extensions = QLineEdit()
        self._extensions.setPlaceholderText(".py .txt .md")
        adv_form.addRow("Extensions:", self._extensions)

        self._context_lines = QSpinBox()
        self._context_lines.setRange(0, 5)
        self._context_lines.setValue(0)
        self._context_lines.setToolTip("Lines of context above/below each content match")
        adv_form.addRow("Context lines:", self._context_lines)

        self._adv_box = adv_box
        layout.addWidget(adv_box)

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
            "content_regex": SearchMode.CONTENT_REGEX,
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
            SearchMode.CONTENT_REGEX: "content_regex",
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
    def scope(self) -> SearchScope:
        return self._scope.currentData()

    @property
    def max_results(self) -> int:
        return self._max_results.value()

    @property
    def case_sensitive(self) -> bool:
        return self._case_sensitive.isChecked()

    @property
    def whole_word(self) -> bool:
        return self._whole_word.isChecked()

    @property
    def context_lines(self) -> int:
        return self._context_lines.value()

    @property
    def exclude_patterns(self) -> list[str]:
        raw = self._exclude.text().strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    @property
    def search_filter(self) -> SearchFilter | None:
        if not self._adv_box.isChecked():
            return None
        import datetime
        min_s = self._min_size.value() or None
        max_s = self._max_size.value() or None
        exts_raw = self._extensions.text().strip()
        exts = frozenset(e if e.startswith(".") else f".{e}" for e in exts_raw.split()) if exts_raw else frozenset()
        after_dt = self._mod_after.date().toPython()
        before_dt = self._mod_before.date().toPython()
        mod_after = datetime.datetime.combine(after_dt, datetime.time.min).timestamp()
        mod_before = datetime.datetime.combine(before_dt, datetime.time.max).timestamp()
        return SearchFilter(
            min_size=min_s, max_size=max_s,
            modified_after=mod_after, modified_before=mod_before,
            extensions=exts,
        )

    @staticmethod
    def get_params(
        root: Path,
        parent: QWidget | None = None,
        *,
        store: SearchTemplateStore | None = None,
        history: list[str] | None = None,
    ) -> tuple[str, SearchMode, int, SearchScope, SearchFilter | None, list[str], bool, bool, int] | None:
        """Show dialog, return (query, mode, max_results, scope, filter, exclude_patterns, case_sensitive, whole_word, context_lines) or None."""
        dlg = SearchDialog(root, parent, store=store, history=history)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return (
                dlg.query, dlg.mode, dlg.max_results, dlg.scope,
                dlg.search_filter, dlg.exclude_patterns,
                dlg.case_sensitive, dlg.whole_word, dlg.context_lines,
            )
        return None
