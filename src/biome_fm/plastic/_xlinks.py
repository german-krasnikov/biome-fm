"""Xlink (cross-repo reference) helpers for Plastic SCM."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Xlink

_XLINK_FMT = "{path}|{server}|{repository}|{branch}|{changeset}"


def parse_xlinks(output: str) -> list[Xlink]:
    result = []
    for line in output.strip().splitlines():
        parts = line.split("|", maxsplit=4)
        if len(parts) < 3:
            continue
        cs = 0
        if len(parts) >= 5:
            try:
                cs = int(parts[4])
            except ValueError:
                pass
        result.append(Xlink(
            path=parts[0].strip(),
            server=parts[1].strip(),
            repo=parts[2].strip(),
            branch=parts[3].strip() if len(parts) >= 4 else "",
            cs_id=cs,
        ))
    return result


def list_xlinks(cwd: Path) -> list[Xlink]:
    out = run_cm(["find", "xlinks", f"--format={_XLINK_FMT}"], cwd=cwd, safe=True)
    return parse_xlinks(out)


def add_xlink(local_path: str, server: str, repo: str, cwd: Path) -> None:
    # ponytail: exact cm xlink flags vary by version — adjust if needed
    run_cm(["xlink", "--add", f"--server={server}", f"--repository={repo}",
            f"--mountpath={local_path}"], cwd=cwd)


def remove_xlink(local_path: str, cwd: Path) -> None:
    run_cm(["xlink", "--remove", f"--mountpath={local_path}"], cwd=cwd)
