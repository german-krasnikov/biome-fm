"""Tests for CommandHistory.push()."""
from biome_fm.commands.base import Command, CommandHistory


class _FakeCmd(Command):
    def __init__(self):
        self.executed = False

    def execute(self):
        self.executed = True

    def undo(self):
        self.executed = False


class _NonUndoable(Command):
    undoable = False

    def execute(self): ...
    def undo(self): ...


def test_push_adds_to_undo_stack():
    h = CommandHistory()
    cmd = _FakeCmd()
    h.push(cmd)
    assert h.can_undo
    h.undo()
    assert not h.can_undo


def test_push_non_undoable_ignored():
    h = CommandHistory()
    h.push(_NonUndoable())
    assert not h.can_undo


def test_push_clears_redo():
    h = CommandHistory()
    cmd1 = _FakeCmd()
    h.execute(cmd1)
    h.undo()
    assert h.can_redo
    h.push(_FakeCmd())
    assert not h.can_redo
