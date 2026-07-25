"""List Plastic SCM branches and switch workspace to a branch or changeset."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Branch, parse_date

_FMT = "{name}|{parent}|{date}|{owner}"


def get_branches(cwd: Path) -> list[Branch]:
    """Return all branches visible from the current workspace.

    Uses: cm find branches --format="{name}|{parent}|{date}|{owner}"
    """
    out = run_cm(["find", "branches", f"--format={_FMT}"], cwd=cwd, safe=True)
    return parse_branches(out)


def parse_branches(output: str) -> list[Branch]:
    results: list[Branch] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 3:
            continue
        if len(parts) >= 4:
            name, parent, date_str, owner = parts
        else:
            name, date_str, owner = parts
            parent = ""
        results.append(Branch(
            name=name.strip(),
            date=parse_date(date_str),
            owner=owner.strip(),
            parent=parent.strip(),
        ))
    return results


def switch_branch(branch: str, cwd: Path) -> None:
    """cm switch br:<branch>. Accepts bare name or "br:/main" form."""
    name = branch if branch.startswith("br:") else f"br:{branch}"
    run_cm(["switch", name], cwd=cwd)


def delete_branch(name: str, cwd: Path) -> None:
    br = name if name.startswith("br:") else f"br:{name}"
    run_cm(["branch", "delete", br], cwd=cwd)


def rename_branch(old: str, new: str, cwd: Path) -> None:
    br = old if old.startswith("br:") else f"br:{old}"
    run_cm(["branch", "rename", br, new], cwd=cwd)


def switch_changeset(cs_id: int, cwd: Path) -> None:
    """cm switch cs:<cs_id> — pinned changeset (detached-head equivalent)."""
    run_cm(["switch", f"cs:{cs_id}"], cwd=cwd)
