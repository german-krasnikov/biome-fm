"""Parse `cm status --all` output into list[PlasticItem]."""
from __future__ import annotations

import re
from pathlib import Path

from ._cm import run_cm
from ._models import PlasticItem, STATUS_LABELS

_CODES = frozenset(STATUS_LABELS)


def get_status(cwd: Path) -> list[PlasticItem]:
    """Return workspace status. Tries --machinereadable first, falls back to plain.

    cm status --all lists every item including private/ignored.
    machinereadable format: CO|/abs/path/to/file
    plain format:           CO  /abs/path/to/file   (leading spaces possible)
    """
    out = run_cm(["status", "--all", "--machinereadable"], cwd=cwd, safe=True)
    if not out.strip():
        out = run_cm(["status", "--all"], cwd=cwd, safe=True)
    return parse_status(out, cwd)


def parse_status(output: str, cwd: Path) -> list[PlasticItem]:
    items: list[PlasticItem] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # machinereadable: "CO|/path/to/file" or "CO|/path|False|NO_MERGES"
        if "|" in line:
            parts = line.split("|")
            if len(parts) < 2:
                continue
            code, path_str = parts[0].strip(), parts[1].strip()
        else:
            # plain: "CO  path/to/file" or "  CO  path/to/file"
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            code, path_str = parts
            # strip trailing cm metadata: " False NO_MERGES", " True", etc.
            path_str = re.sub(r'\s+(?:True|False)(?:\s+\S+)*$', '', path_str)

        code = code.upper()
        if code not in _CODES:
            continue

        p = Path(path_str)
        if not p.is_absolute():
            p = (cwd / p).resolve()
        items.append(PlasticItem(status=code, path=p))
    return items
