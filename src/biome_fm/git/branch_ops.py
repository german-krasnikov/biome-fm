"""Pure-Python git branch operations — no Qt."""
from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired

from biome_fm.git.run import run_git

_TIMEOUT = 5


def list_branches(repo: Path) -> list[str]:
    """Return all local branches. Empty list if not a git repo."""
    raw = run_git(["branch", "--list"], cwd=repo, timeout=_TIMEOUT, safe=True)
    return [line[2:].strip() for line in raw.splitlines() if len(line) >= 2 and line.strip()]


def current_branch(repo: Path) -> str:
    """Return current branch name, '(detached)' on detached HEAD, '' on error."""
    name = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, timeout=_TIMEOUT, safe=True).strip()
    if not name:
        return ""
    return "(detached)" if name == "HEAD" else name


def switch_branch(repo: Path, branch: str) -> None:
    """Switch to branch. Raises RuntimeError on failure (dirty tree, etc.)."""
    try:
        run_git(["switch", branch], cwd=repo, timeout=10)
    except (CalledProcessError, OSError, TimeoutExpired) as exc:
        msg = exc.stderr.strip() if isinstance(exc, CalledProcessError) else str(exc)
        raise RuntimeError(msg or f"git switch {branch} failed") from exc
