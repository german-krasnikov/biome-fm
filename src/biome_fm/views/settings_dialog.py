"""SettingsDialog — passive view for application settings."""
from __future__ import annotations

from biome_fm.qt import (
    Qt,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # ── General ───────────────────────────────────────────────────────────
        general = QWidget()
        gl = QFormLayout(general)
        self._hidden_cb = QCheckBox("Show hidden files")
        self._sync_cb = QCheckBox("Sync browsing")
        self._colors_cb = QCheckBox("File type colors")
        gl.addRow(self._hidden_cb)
        gl.addRow(self._sync_cb)
        gl.addRow(self._colors_cb)
        self._tabs.addTab(general, "General")

        # ── Appearance ────────────────────────────────────────────────────────
        appearance = QWidget()
        al = QFormLayout(appearance)
        self._theme_combo = QComboBox()
        al.addRow("Theme:", self._theme_combo)
        self._glass_cb = QCheckBox("Glass effect")
        al.addRow(self._glass_cb)
        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(10, 90)
        self._opacity_slider.setSingleStep(5)
        self._opacity_label = QLabel("47%")
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        opacity_row.addWidget(self._opacity_slider)
        opacity_row.addWidget(self._opacity_label)
        al.addRow("Glass opacity:", opacity_row)
        self._tabs.addTab(appearance, "Appearance")

        # ── AI ────────────────────────────────────────────────────────────────
        ai = QWidget()
        ail = QFormLayout(ai)
        self._ai_provider = QComboBox()
        self._ai_provider.addItems(["claude", "openai", "ollama"])
        self._claude_key = QLineEdit()
        self._claude_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key = QLineEdit()
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._ollama_url = QLineEdit()
        self._ollama_model = QLineEdit()
        ail.addRow("Provider:", self._ai_provider)
        ail.addRow("Claude Key:", self._claude_key)
        ail.addRow("OpenAI Key:", self._openai_key)
        ail.addRow("Ollama URL:", self._ollama_url)
        ail.addRow("Ollama Model:", self._ollama_model)
        self._tabs.addTab(ai, "AI")

        # ── Plugins ───────────────────────────────────────────────────────────
        plugins = QWidget()
        pl = QVBoxLayout(plugins)
        pl.addWidget(QLabel("Installed plugins:"))
        self._plugins_list = QListWidget()
        pl.addWidget(self._plugins_list)
        self._tabs.addTab(plugins, "Plugins")

        # ── Buttons ───────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── SettingsViewProtocol ──────────────────────────────────────────────────

    def set_theme(self, name: str) -> None:
        self._theme_combo.setCurrentText(name)

    def get_theme(self) -> str:
        return self._theme_combo.currentText()

    def set_show_hidden(self, val: bool) -> None:
        self._hidden_cb.setChecked(val)

    def get_show_hidden(self) -> bool:
        return self._hidden_cb.isChecked()

    def set_sync_browsing(self, val: bool) -> None:
        self._sync_cb.setChecked(val)

    def get_sync_browsing(self) -> bool:
        return self._sync_cb.isChecked()

    def set_file_type_colors(self, val: bool) -> None:
        self._colors_cb.setChecked(val)

    def get_file_type_colors(self) -> bool:
        return self._colors_cb.isChecked()

    def set_ai_provider(self, name: str) -> None:
        self._ai_provider.setCurrentText(name)

    def get_ai_provider(self) -> str:
        return self._ai_provider.currentText()

    def set_ai_keys(self, claude: str, openai: str) -> None:
        self._claude_key.setText(claude)
        self._openai_key.setText(openai)

    def get_ai_keys(self) -> tuple[str, str]:
        return (self._claude_key.text(), self._openai_key.text())

    def set_themes_list(self, names: list[str]) -> None:
        self._theme_combo.clear()
        self._theme_combo.addItems(names)

    def set_plugins_list(self, names: list[str]) -> None:
        self._plugins_list.clear()
        self._plugins_list.addItems(names)

    def set_glass(self, val: bool) -> None:
        self._glass_cb.setChecked(val)

    def get_glass(self) -> bool:
        return self._glass_cb.isChecked()

    def set_glass_opacity(self, val: int) -> None:
        self._opacity_slider.setValue(val)

    def get_glass_opacity(self) -> int:
        return self._opacity_slider.value()

    def set_ollama(self, url: str, model: str) -> None:
        self._ollama_url.setText(url)
        self._ollama_model.setText(model)

    def get_ollama(self) -> tuple[str, str]:
        return (self._ollama_url.text(), self._ollama_model.text())
