"""F257 — Shell Variables Extended ($D/$s/$S)."""
import shlex
from pathlib import Path

from biome_fm.utils.shell_vars import expand_shell_vars

CWD = Path("/home/user/active")
OTHER = Path("/home/user/other")
FILE1 = Path("/home/user/active/foo.txt")
FILE2 = Path("/home/user/active/bar.md")


def _expand(cmd: str, files: list[Path] | None = None) -> str:
    return expand_shell_vars(cmd, files=files or [], cwd=CWD, other_cwd=OTHER)


def test_expand_f_variable() -> None:
    """$F = all selected files, space-separated quoted (existing behavior, regression)."""
    result = _expand("zip out.zip $F", files=[FILE1, FILE2])
    assert shlex.quote(str(FILE1)) in result
    assert shlex.quote(str(FILE2)) in result


def test_expand_s_multiple_selection() -> None:
    """$s = space-separated shlex-quoted selected paths (new alias)."""
    result = _expand("cp $s /dest/", files=[FILE1, FILE2])
    assert shlex.quote(str(FILE1)) in result
    assert shlex.quote(str(FILE2)) in result


def test_expand_S_single_quoted() -> None:
    """$S = all paths joined then single-quoted."""
    result = _expand("tool --files $S", files=[FILE1, FILE2])
    expected = shlex.quote(f"{FILE1} {FILE2}")
    assert expected in result


def test_expand_D_other_cwd() -> None:
    """$D = opposite pane path, quoted."""
    result = _expand("rsync $d/ $D/", files=[])
    assert shlex.quote(str(OTHER)) in result


def test_no_vars_unchanged() -> None:
    assert _expand("ls -la") == "ls -la"
