"""Test that CLI subcommands dispatch correctly without touching Qt."""

import sys


def test_subcommand_handled_before_qt_start(monkeypatch, capsys):
    """dispatch() returns a real int for known subcommands — Qt never starts."""
    from biome_fm.mcp.cli import UNHANDLED, dispatch

    qt_before = "PySide6.QtWidgets" in sys.modules
    result = dispatch(["version"])
    assert result is not UNHANDLED
    assert isinstance(result, int)
    # dispatch() must not pull in Qt — only already-loaded modules are acceptable
    qt_after = "PySide6.QtWidgets" in sys.modules
    assert qt_before == qt_after, "dispatch() imported PySide6.QtWidgets as a side effect"


def test_dispatch_unhandled_does_not_exit(monkeypatch):
    """Unknown subcommands return UNHANDLED so Qt startup proceeds normally."""
    from biome_fm.mcp.cli import UNHANDLED, dispatch

    result = dispatch(["--some-qt-flag"])
    assert result is UNHANDLED

    result = dispatch([])
    assert result is UNHANDLED
