"""Total Commander-style variable expansion for shell commands."""
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

    # $F before $f to avoid prefix collision
    replacements = [
        ("$F", " ".join(f'"{p}"' for p in files) if files else f'"{cwd}"'),
        ("$f", f'"{first}"'),
        ("$d", f'"{cwd}"'),
        ("$t", f'"{other_cwd}"'),
        ("$n", f'"{first.stem}"'),
        ("$e", f'"{first.suffix}"'),
    ]
    for var, val in replacements:
        cmd = cmd.replace(var, val)
    return cmd
