"""List Plastic SCM labels."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Label, parse_date

_FMT = "{name}|{changeset}|{date}"


def create_label(name: str, cs_id: int, cwd: Path) -> None:
    run_cm(["label", "create", name, f"cs:{cs_id}"], cwd=cwd)


def delete_label(name: str, cwd: Path) -> None:
    run_cm(["label", "delete", name], cwd=cwd)


def rename_label(old: str, new: str, cwd: Path) -> None:
    run_cm(["label", "rename", old, new], cwd=cwd)


def get_labels(cwd: Path) -> list[Label]:
    """Return all labels.

    Uses: cm find labels --format="{name}|{changeset}|{date}"
    """
    out = run_cm(["find", "labels", f"--format={_FMT}"], cwd=cwd, safe=True)
    return parse_labels(out)


def parse_labels(output: str) -> list[Label]:
    results: list[Label] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        name, cs_str, date_str = parts
        try:
            cs_id = int(cs_str.strip())
        except ValueError:
            continue
        results.append(Label(
            name=name.strip(),
            changeset=cs_id,
            date=parse_date(date_str),
        ))
    return results
