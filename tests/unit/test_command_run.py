"""Test expand_shell_vars in context of UserCommand.command."""
from pathlib import Path

from biome_fm.models.command_store import UserCommand
from biome_fm.utils.shell_vars import expand_shell_vars


def test_expand_placeholders_in_user_command(tmp_path: Path) -> None:
    cwd = tmp_path / "src"
    other = tmp_path / "dst"
    f = cwd / "note.txt"
    cmd = UserCommand(id="u", label="U", command="cp $f $t")
    expanded = expand_shell_vars(cmd.command, files=[f], cwd=cwd, other_cwd=other)
    assert f'"{f}"' in expanded
    assert f'"{other}"' in expanded
