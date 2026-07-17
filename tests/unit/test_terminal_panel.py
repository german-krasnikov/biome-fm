"""Unit tests for terminal panel — no Qt needed."""
from biome_fm.views.terminal_panel import _default_shell


def test_default_shell_nonempty():
    shell = _default_shell()
    assert shell
    assert isinstance(shell, str)
