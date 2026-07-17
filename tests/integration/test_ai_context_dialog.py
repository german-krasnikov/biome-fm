"""Integration test for AIContextDialog."""
from PySide6.QtWidgets import QLabel
from biome_fm.ai.provider import NoOpProvider
from biome_fm.views.ai_context_dialog import AIContextDialog


def test_dialog_shows_no_ai_label(qtbot):
    dlg = AIContextDialog(["file.py", "data.csv"], NoOpProvider())
    qtbot.addWidget(dlg)
    dlg.show()
    texts = [lbl.text() for lbl in dlg.findChildren(QLabel)]
    assert any("AI not configured" in t for t in texts)
