"""Unit tests for glass module."""
from unittest.mock import MagicMock, patch


def test_glass_lib_available():
    from biome_fm.views.glass import _HAS_LIB
    assert _HAS_LIB is True  # pyqt-liquidglass installed


def test_prepare_glass_calls_library():
    from biome_fm.views import glass
    window = MagicMock()
    with patch.object(glass, "_glass") as mock_lib:
        result = glass.prepare_glass(window)
    mock_lib.prepare_window_for_glass.assert_called_once_with(window)
    assert result is True


def test_enable_glass_calls_library():
    from biome_fm.views import glass
    window = MagicMock()
    with patch.object(glass, "_glass") as mock_lib:
        result = glass.enable_glass(window)
    mock_lib.apply_glass_to_window.assert_called_once_with(window)
    assert result is True


def test_disable_glass_calls_library():
    from biome_fm.views import glass
    window = MagicMock()
    with patch.object(glass, "_glass") as mock_lib:
        glass.disable_glass(window)
    mock_lib.remove_glass_effect.assert_called_once_with(window)
