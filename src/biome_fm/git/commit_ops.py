"""Pure-Python git commit operations — no Qt."""
from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError

from biome_fm.git.run import run_git

_TIMEOUT = 10


def stage_files(repo: Path, paths: list[Path]) -> None:
    """Stage files via git add."""
    try:
        run_git(["add", "--"] + [str(p) for p in paths], cwd=repo, timeout=_TIMEOUT)
    except CalledProcessError as e:
        raise RuntimeError(e.stderr.strip() or "git add failed") from e


def unstage_files(repo: Path, paths: list[Path]) -> None:
    """Unstage files via git reset HEAD."""
    try:
        run_git(["reset", "HEAD", "--"] + [str(p) for p in paths], cwd=repo, timeout=_TIMEOUT)
    except CalledProcessError as e:
        raise RuntimeError(e.stderr.strip() or "git reset failed") from e


def staged_files(repo: Path) -> list[str]:
    """Return list of staged file paths. Empty list if not a git repo."""
    raw = run_git(["diff", "--cached", "--name-only"], cwd=repo, timeout=_TIMEOUT, safe=True)
    return [line for line in raw.splitlines() if line]


def staged_diff(repo: Path) -> str:
    """Return full staged diff. Empty string if not a git repo or no changes."""
    return run_git(["diff", "--cached"], cwd=repo, timeout=_TIMEOUT, safe=True)


def commit(repo: Path, message: str) -> str:
    """Commit staged files. Returns short hash. Raises ValueError/RuntimeError."""
    if not message.strip():
        raise ValueError("commit message cannot be empty")
    try:
        run_git(["commit", "-m", message], cwd=repo, timeout=_TIMEOUT)
    except CalledProcessError as e:
        raise RuntimeError(e.stderr.strip() or e.stdout.strip() or "git commit failed") from e
    return run_git(["rev-parse", "--short", "HEAD"], cwd=repo, timeout=_TIMEOUT, safe=True).strip()
