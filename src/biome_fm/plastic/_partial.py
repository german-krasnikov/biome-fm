"""cm partial workspace helpers."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm


def get_partial_status(cwd: Path) -> str:
    return run_cm(["partial", "status"], cwd=cwd, safe=True)


def configure_partial(cwd: Path) -> str:
    return run_cm(["partial", "configure"], cwd=cwd, safe=True)


def add_partial(path: str, cwd: Path) -> None:
    run_cm(["partial", "add", path], cwd=cwd)


def remove_partial(path: str, cwd: Path) -> None:
    run_cm(["partial", "remove", path], cwd=cwd)
