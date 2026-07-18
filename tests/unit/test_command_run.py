"""Test expand_shell_vars in context of UserCommand.command."""
import shlex
from pathlib import Path

from biome_fm.models.command_store import UserCommand
from biome_fm.utils.shell_vars import expand_shell_vars


def test_expand_placeholders_in_user_command(tmp_path: Path) -> None:
    cwd = tmp_path / "src"
    other = tmp_path / "dst"
    f = cwd / "note.txt"
    cmd = UserCommand(id="u", label="U", command="cp $f $t")
    expanded = expand_shell_vars(cmd.command, files=[f], cwd=cwd, other_cwd=other)
    assert shlex.quote(str(f)) in expanded
    assert shlex.quote(str(other)) in expanded


def test_expand_shell_vars_quotes_special_chars(tmp_path: Path) -> None:
    """shlex.quote handles filenames with spaces and quotes correctly."""
    cwd = tmp_path
    f = cwd / "my file.txt"
    expanded = expand_shell_vars("echo $f", files=[f], cwd=cwd, other_cwd=cwd)
    # shlex.split should round-trip back to the original path
    parts = shlex.split(expanded)
    assert str(f) in parts
