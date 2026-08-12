"""Plastic SCM changelist operations via cm changelist."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import STATUS_LABELS, PlasticItem

_CODES = frozenset(STATUS_LABELS)


def parse_changelist_status(output: str, cwd: Path) -> dict[str, list[PlasticItem]]:
    """Parse `cm status --changelists` output.

    Expected format:
        Changelist 'name':
          CO|/abs/path
          AD|/abs/path
    """
    result: dict[str, list[PlasticItem]] = {}
    current: str | None = None
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Changelist '") and stripped.endswith("':"):
            current = stripped[len("Changelist '"):-2]
            result.setdefault(current, [])
            continue
        if current is None:
            continue
        if "|" not in stripped:
            continue
        code, _, path_str = stripped.partition("|")
        code = code.strip().upper()
        if code not in _CODES:
            continue
        p = Path(path_str.strip())
        if not p.is_absolute():
            p = (cwd / p).resolve()
        result[current].append(PlasticItem(status=code, path=p))
    return result


def create_changelist(name: str, cwd: Path, description: str = "") -> None:
    args = ["changelist", "create", name]
    if description:
        args.append(description)
    run_cm(args, cwd=cwd)


def delete_changelist(name: str, cwd: Path) -> None:
    run_cm(["changelist", "delete", name], cwd=cwd)


def add_to_changelist(name: str, paths: list[Path], cwd: Path) -> None:
    run_cm(["changelist", name, "add", *(str(p) for p in paths)], cwd=cwd)


def remove_from_changelist(name: str, paths: list[Path], cwd: Path) -> None:
    run_cm(["changelist", name, "rm", *(str(p) for p in paths)], cwd=cwd)
