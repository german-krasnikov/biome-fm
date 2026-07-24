"""Integration tests for FilterBar preset combo."""
import pytest


@pytest.fixture()
def bar(qtbot):
    from biome_fm.views.filter_bar import FilterBar

    b = FilterBar()
    qtbot.addWidget(b)
    b.set_debounce_ms(0)
    b.activate()
    return b


def test_preset_selection_sets_text(qtbot, bar):
    from biome_fm.views.filter_bar import FILTER_PRESETS

    received = []
    bar.filter_changed.connect(received.append)
    bar._preset_combo.setCurrentIndex(1)  # first real preset
    qtbot.waitUntil(lambda: len(received) > 0, timeout=500)

    _, expected_text = FILTER_PRESETS[0]
    assert bar._edit.text() == expected_text
    assert received[-1] == expected_text


def test_manual_type_resets_preset_combo(qtbot, bar):
    # Bypass _on_preset_selected so the combo stays at 1 (simulates a persistent selection state)
    bar._preset_combo.blockSignals(True)
    bar._preset_combo.setCurrentIndex(1)
    bar._preset_combo.blockSignals(False)
    assert bar._preset_combo.currentIndex() == 1  # sanity: combo is non-zero
    bar._edit.setText("hello")
    assert bar._preset_combo.currentIndex() == 0


def test_deactivate_resets_combo(qtbot, bar):
    bar._preset_combo.setCurrentIndex(2)
    bar.deactivate()
    assert bar._preset_combo.currentIndex() == 0
