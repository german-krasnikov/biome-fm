"""Integration tests for Item #32 — JumpBar/ContextBar objectName theming."""
import pytest


@pytest.mark.usefixtures("qapp")
def test_jump_bar_label_object_name(qtbot):
    from biome_fm.views.jump_bar import JumpBar
    bar = JumpBar()
    qtbot.addWidget(bar)
    assert bar._label.objectName() == "jump_bar_label"
    assert bar._label.styleSheet() == ""


@pytest.mark.usefixtures("qapp")
def test_chip_object_name(qtbot):
    from biome_fm.views._context_bar import _Chip
    chip = _Chip("test.txt", 0)
    qtbot.addWidget(chip)
    assert chip.objectName() == "context_chip"
    assert "2a2a3a" not in chip.styleSheet()
