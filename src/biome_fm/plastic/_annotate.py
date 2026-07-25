"""Plastic SCM line-level blame — thin wrapper around `cm annotate`."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import BlameLine, parse_date

_ANN_FMT = "{line}|{owner}|{changeset}|{date}|{content}"


def get_blame(path: Path, cwd: Path) -> list[BlameLine]:
    out = run_cm(
        ["annotate", str(path), f"--format={_ANN_FMT}"],
        cwd=cwd,
        safe=True,
    )
    return parse_blame(out)


def parse_blame(output: str) -> list[BlameLine]:
    lines: list[BlameLine] = []
    for raw in output.splitlines():
        parts = raw.split("|", maxsplit=4)  # content may contain |
        if len(parts) < 5:
            continue
        try:
            lines.append(BlameLine(
                line_no=int(parts[0]),
                owner=parts[1],
                cs_id=int(parts[2]),
                date=parse_date(parts[3]),
                content=parts[4],
            ))
        except (ValueError, IndexError):
            continue
    return lines
