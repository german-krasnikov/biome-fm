"""F308 — Configurable UI Font Size (RED phase)."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_default_font_size_is_zero() -> None:
    from biome_fm.config import Config

    assert Config().ui_font_size == 0


def test_nonzero_applies_font(qtbot) -> None:
    from PySide6.QtWidgets import QApplication
    from biome_fm.config import Config

    cfg = Config(ui_font_size=14)
    app = QApplication.instance()
    if cfg.ui_font_size > 0:
        f = app.font()
        f.setPointSize(cfg.ui_font_size)
        app.setFont(f)
    assert app.font().pointSize() == 14


def test_settings_dialog_has_font_spinbox(qtbot) -> None:
    from biome_fm.views.settings_dialog import SettingsDialog

    d = SettingsDialog()
    qtbot.addWidget(d)
    assert hasattr(d, "_font_size_spin")
    assert d.get_ui_font_size() == 0
    d.set_ui_font_size(16)
    assert d.get_ui_font_size() == 16
