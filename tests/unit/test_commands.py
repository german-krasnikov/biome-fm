"""Tests for Command base and CommandHistory."""

from biome_fm.commands.base import Command, CommandHistory


class FakeCommand(Command):
    def __init__(self) -> None:
        self.executed = False
        self.undone = False

    def execute(self) -> None:
        self.executed = True

    def undo(self) -> None:
        self.undone = True


class TestCommandHistory:
    def test_execute_runs_command(self) -> None:
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        assert cmd.executed

    def test_undo_reverses_last(self) -> None:
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        history.undo()
        assert cmd.undone

    def test_redo_re_executes(self) -> None:
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        history.undo()

        cmd.executed = False
        history.redo()
        assert cmd.executed

    def test_undo_empty_is_noop(self) -> None:
        history = CommandHistory()
        history.undo()  # should not raise

    def test_redo_empty_is_noop(self) -> None:
        history = CommandHistory()
        history.redo()  # should not raise

    def test_execute_clears_redo_stack(self) -> None:
        history = CommandHistory()
        cmd1 = FakeCommand()
        cmd2 = FakeCommand()
        history.execute(cmd1)
        history.undo()
        history.execute(cmd2)
        assert not history.can_redo

    def test_max_depth_evicts_oldest(self) -> None:
        history = CommandHistory(max_depth=2)
        cmds = [FakeCommand() for _ in range(3)]
        for c in cmds:
            history.execute(c)
        history.undo()
        history.undo()
        assert not history.can_undo  # 3rd undo impossible, oldest was evicted
