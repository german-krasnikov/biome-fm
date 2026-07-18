"""F311 — Focus Indicator Enhancement (RED phase)."""
from __future__ import annotations

from pathlib import Path


def test_focus_rules_in_qss() -> None:
    tmpl = (
        Path(__file__).parent.parent.parent
        / "src/biome_fm/themes/_base.qss.tmpl"
    )
    content = tmpl.read_text(encoding="utf-8")
    assert "QPushButton:focus" in content
    assert "QTableView:focus" in content
    assert "QComboBox:focus" in content
