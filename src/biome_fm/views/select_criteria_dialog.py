"""Dialog for multi-criteria file selection (F221)."""
from __future__ import annotations

from biome_fm.models.select_criteria import SelectCriteria
from biome_fm.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class SelectByAttrDialog(QDialog):
    """Dialog for building a SelectCriteria from user input."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select by Criteria")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_glob = QLineEdit()
        self._name_glob.setPlaceholderText("e.g. *.py")
        form.addRow("Name pattern:", self._name_glob)

        self._extensions = QLineEdit()
        self._extensions.setPlaceholderText("e.g. .py, .txt")
        form.addRow("Extensions:", self._extensions)

        size_row = QHBoxLayout()
        self._min_size = QSpinBox()
        self._min_size.setRange(0, 2_000_000)
        self._min_size.setSuffix(" KB")
        self._max_size = QSpinBox()
        self._max_size.setRange(0, 2_000_000)
        self._max_size.setSuffix(" KB")
        size_row.addWidget(QLabel("Min:"))
        size_row.addWidget(self._min_size)
        size_row.addWidget(QLabel("Max:"))
        size_row.addWidget(self._max_size)
        form.addRow("Size range:", size_row)

        age_row = QHBoxLayout()
        self._min_age = QSpinBox()
        self._min_age.setRange(0, 36500)
        self._min_age.setSuffix(" days")
        self._max_age = QSpinBox()
        self._max_age.setRange(0, 36500)
        self._max_age.setSuffix(" days")
        age_row.addWidget(QLabel("Min age:"))
        age_row.addWidget(self._min_age)
        age_row.addWidget(QLabel("Max age:"))
        age_row.addWidget(self._max_age)
        form.addRow("Age range:", age_row)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_criteria(self) -> SelectCriteria:
        exts = [e.strip().lower() for e in self._extensions.text().split(",") if e.strip()]
        # ensure extensions start with dot
        exts = [e if e.startswith(".") else f".{e}" for e in exts]
        return SelectCriteria(
            name_glob=self._name_glob.text().strip(),
            extensions=exts,
            min_size=self._min_size.value() * 1024,
            max_size=self._max_size.value() * 1024,
            min_age_days=self._min_age.value(),
            max_age_days=self._max_age.value(),
        )
