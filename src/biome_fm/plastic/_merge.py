"""Plastic SCM merge operations."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm


def merge_branch(branch: str, cwd: Path, *, preview: bool = False,
                 resolve: str = "", semantic: bool = False) -> str:
    """cm merge br:<branch>. resolve: '' | 'keepsource' | 'keepdestination'"""
    name = branch if branch.startswith("br:") else f"br:{branch}"
    args = ["merge", name]
    if preview:
        args.append("--preview")
    if resolve:
        args.append(f"--{resolve}")
    if semantic:
        args.append("--semantic")
    return run_cm(args, cwd=cwd, timeout=60, safe=preview)


def merge_changeset(cs_id: int, cwd: Path, *, cherrypick: bool = False,
                    resolve: str = "") -> str:
    """cm merge cs:<cs_id>."""
    args = ["merge", f"cs:{cs_id}"]
    if cherrypick:
        args.extend(["--merge", "--cherrypicking"])
    if resolve:
        args.append(f"--{resolve}")
    return run_cm(args, cwd=cwd, timeout=60)
