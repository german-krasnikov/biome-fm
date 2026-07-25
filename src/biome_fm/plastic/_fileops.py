"""Plastic SCM file operations — add, remove, move."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm


def add(paths: list[Path], cwd: Path, recursive: bool = False) -> None:
    args = ["add"]
    if recursive:
        args.append("--recursive")
    args.extend(str(p) for p in paths)
    run_cm(args, cwd=cwd)


def remove(path: Path, cwd: Path) -> None:
    run_cm(["remove", str(path)], cwd=cwd)


def move(src: Path, dst: Path, cwd: Path) -> None:
    run_cm(["move", str(src), str(dst)], cwd=cwd)
