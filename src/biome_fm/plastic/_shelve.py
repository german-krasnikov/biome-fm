"""Plastic SCM shelve/unshelve operations via cm shelveset."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Shelve, parse_date

_FMT = "{id}|{date}|{owner}|{comment}"


def shelve(msg: str, cwd: Path, paths: list[Path] | None = None) -> None:
    """Shelve pending changes. Raises CMError on failure."""
    args = ["shelveset", "create", f"-c={msg}"]
    if paths:
        args.extend(str(p) for p in paths)
    run_cm(args, cwd=cwd, timeout=None)


def unshelve(shelve_id: int, cwd: Path) -> None:
    """Apply (unshelve) a shelve by id. Raises CMError on failure."""
    run_cm(["shelveset", "apply", str(shelve_id)], cwd=cwd, timeout=None)


def delete_shelve(shelve_id: int, cwd: Path) -> None:
    """Delete a shelve by id. Raises CMError on failure."""
    run_cm(["shelveset", "delete", str(shelve_id)], cwd=cwd, timeout=None)


def get_shelves(cwd: Path) -> list[Shelve]:
    """Return all shelves, oldest first."""
    out = run_cm(["find", "shelves", f"--format={_FMT}"], cwd=cwd, safe=True)
    return parse_shelves(out)


def parse_shelves(output: str) -> list[Shelve]:
    results: list[Shelve] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # comment may contain | so cap at 3 splits
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        id_str, date_str, owner, comment = parts
        try:
            shelve_id = int(id_str.strip())
        except ValueError:
            continue
        results.append(Shelve(
            shelve_id=shelve_id,
            date=parse_date(date_str),
            owner=owner.strip(),
            comment=comment.strip(),
        ))
    return results
