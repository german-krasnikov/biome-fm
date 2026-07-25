"""Plastic SCM file history — thin wrapper around `cm history`."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Revision, parse_date

_HIST_FMT = "{changesetid}|{date}|{owner}|{branch}|{id}|{comment}"


def get_file_history(path: Path, cwd: Path, limit: int = 50) -> list[Revision]:
    out = run_cm(
        ["history", str(path), f"--limit={limit}", f"--format={_HIST_FMT}"],
        cwd=cwd,
        safe=True,
    )
    return parse_history(out)


def parse_history(output: str) -> list[Revision]:
    revisions: list[Revision] = []
    for line in output.splitlines():
        parts = line.split("|", maxsplit=5)
        if len(parts) < 6:
            continue
        try:
            revisions.append(Revision(
                cs_id=int(parts[0]),
                date=parse_date(parts[1]),
                owner=parts[2],
                branch=parts[3],
                rev_id=int(parts[4]),
                comment=parts[5],
            ))
        except (ValueError, IndexError):
            continue
    return revisions
