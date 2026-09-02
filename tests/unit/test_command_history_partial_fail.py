"""Unit tests for CommandHistory auto-rollback on partial execute failure (C02)."""

import pytest

from biome_fm.commands.base import Command, CommandHistory


class PartialCmd(Command):
    """Command that raises on execute() after setting partial state. Records undo calls."""

    def __init__(self) -> None:
        self.undo_called = False

    def execute(self) -> None:
        raise RuntimeError("partial failure")

    def undo(self) -> None:
        self.undo_called = True


def test_partial_execute_triggers_undo_and_not_pushed() -> None:
    """C02: when execute() raises, undo() is called and cmd is not pushed to undo stack."""
    history = CommandHistory()
    cmd = PartialCmd()

    with pytest.raises(RuntimeError, match="partial failure"):
        history.execute(cmd)

    assert cmd.undo_called is True
    assert history.can_undo is False
