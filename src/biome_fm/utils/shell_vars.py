"""Total Commander-style variable expansion for shell commands."""
import shlex
from pathlib import Path


def expand_shell_vars(
    cmd: str,
    *,
    files: list[Path],
    cwd: Path,
    other_cwd: Path,
) -> str:
    """Expand $F $f $d $t $n $e in cmd before passing to shell."""
    first = files[0] if files else cwd

    # $F before $f, $S before $s, $D before $d to avoid prefix collisions
    _files_str = " ".join(shlex.quote(str(p)) for p in files) if files else shlex.quote(str(cwd))
    replacements = [
        ("$F", _files_str),
        ("$S", shlex.quote(" ".join(str(p) for p in files)) if files else shlex.quote(str(cwd))),
        ("$s", _files_str),
        ("$D", shlex.quote(str(other_cwd))),
        ("$f", shlex.quote(str(first))),
        ("$d", shlex.quote(str(cwd))),
        ("$t", shlex.quote(str(other_cwd))),
        ("$n", shlex.quote(first.stem)),
        ("$e", shlex.quote(first.suffix)),
    ]
    for var, val in replacements:
        cmd = cmd.replace(var, val)
    return cmd
