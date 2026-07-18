import shlex
from pathlib import Path

from biome_fm.utils.shell_vars import expand_shell_vars

CWD   = Path("/home/user/docs")
OTHER = Path("/home/user/pics")
FILE1 = Path("/home/user/docs/foo.txt")
FILE2 = Path("/home/user/docs/bar.md")


def expand(cmd, files=None):
    return expand_shell_vars(cmd, files=files or [], cwd=CWD, other_cwd=OTHER)


def _q(p) -> str:
    """Expected shell-quoted form for a path."""
    return shlex.quote(str(p))


def test_no_placeholders_unchanged():
    assert expand("ls -la") == "ls -la"


def test_expand_d_cwd():
    result = expand("cd $d")
    assert result == f"cd {_q(CWD)}"


def test_expand_t_other_cwd():
    result = expand("diff $t $d")
    assert result == f"diff {_q(OTHER)} {_q(CWD)}"


def test_expand_f_single_file():
    result = expand("open $f", files=[FILE1])
    assert result == f"open {_q(FILE1)}"


def test_expand_F_multiple_files():
    result = expand("zip out.zip $F", files=[FILE1, FILE2])
    assert result == f"zip out.zip {_q(FILE1)} {_q(FILE2)}"


def test_expand_n_stem():
    result = expand("echo $n", files=[FILE1])
    assert result == f"echo {_q('foo')}"


def test_expand_e_extension():
    result = expand("echo $e", files=[FILE1])
    assert result == f"echo {_q('.txt')}"


def test_empty_files_fallback():
    # $f with no files → falls back to cwd
    result = expand("open $f", files=[])
    assert result == f"open {_q(CWD)}"


def test_F_before_f_order():
    # both $F and $f in same command — $F must not be corrupted
    result = expand("zip $F && open $f", files=[FILE1, FILE2])
    assert result == f"zip {_q(FILE1)} {_q(FILE2)} && open {_q(FILE1)}"


def test_special_chars_in_filename(tmp_path: Path) -> None:
    """shlex.quote handles filenames with spaces and special chars safely."""
    tricky = tmp_path / "my file's name.txt"
    result = expand_shell_vars("echo $f", files=[tricky], cwd=tmp_path, other_cwd=tmp_path)
    # round-trip via shlex.split must recover the original path
    parts = shlex.split(result)
    assert str(tricky) in parts
