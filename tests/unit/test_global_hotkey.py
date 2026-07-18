"""F321 — Global hotkey: register_global_hotkey with optional pynput."""
import sys
from unittest.mock import MagicMock, patch


def test_returns_none_without_pynput():
    """Returns None gracefully when pynput is not installed."""
    with patch.dict(sys.modules, {"pynput": None, "pynput.keyboard": None}):
        sys.modules.pop("biome_fm.utils.global_hotkey", None)
        from biome_fm.utils.global_hotkey import register_global_hotkey
        result = register_global_hotkey("ctrl+alt+b", lambda: None)
        assert result is None
        sys.modules.pop("biome_fm.utils.global_hotkey", None)


def test_register_returns_handle():
    """Returns a listener handle when pynput is available."""
    mock_pynput = MagicMock()
    mock_keyboard = MagicMock()
    mock_listener = MagicMock()
    mock_keyboard.GlobalHotKeys.return_value = mock_listener
    mock_pynput.keyboard = mock_keyboard

    with patch.dict(sys.modules, {"pynput": mock_pynput, "pynput.keyboard": mock_keyboard}):
        sys.modules.pop("biome_fm.utils.global_hotkey", None)
        from biome_fm.utils.global_hotkey import register_global_hotkey
        cb = lambda: None
        result = register_global_hotkey("ctrl+alt+b", cb)
        assert result is not None
        sys.modules.pop("biome_fm.utils.global_hotkey", None)
