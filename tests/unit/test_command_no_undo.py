"""Guard: Command has no undo attribute; CommandHistory is not exported."""
import biome_fm.commands.base as base_mod
import biome_fm.commands as cmds_pkg


def test_command_has_no_undo():
    assert not hasattr(base_mod.Command, "undo")
    assert not hasattr(base_mod.Command, "undoable")


def test_commandhistory_not_in_module():
    assert not hasattr(base_mod, "CommandHistory")


def test_commands_package_has_no_commandhistory():
    # commands/__init__.py is empty — CommandHistory was never re-exported
    assert not hasattr(cmds_pkg, "CommandHistory")
