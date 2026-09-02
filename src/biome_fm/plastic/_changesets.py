"""Parse `cm find changesets` output into list[Changeset]."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Changeset, parse_date

# Format string passed to `cm find changesets --format=...`
# Fields: changesetid, date, owner, branch, comment
_FMT = "{changesetid}|{date}|{owner}|{branch}|{comment}"

# Operations: checkin, update, undo
def checkin(message: str, cwd: Path, paths: list[Path] | None = None) -> None:
    """Commit selected files (or all if paths is None/empty). Raises CMError on failure."""
    args = ["checkin", f"-c={message}"]
    if paths:
        args.extend(str(p) for p in paths)
    run_cm(args, cwd=cwd)


def update(cwd: Path) -> None:
    """Update workspace to latest. Raises CMError on failure."""
    run_cm(["update"], cwd=cwd)


def undo(path: Path, cwd: Path) -> None:
    """Undo local changes to *path*. Raises CMError on failure."""
    run_cm(["undo", str(path)], cwd=cwd)


def undo_all(cwd: Path) -> None:
    """Undo all local changes. cm undo --all"""
    run_cm(["undo", "--all"], cwd=cwd)


def undo_keep(path: Path, cwd: Path) -> None:
    """Undo but keep local file on disk. cm undo --keep <path>"""
    run_cm(["undo", "--keep", str(path)], cwd=cwd)


def edit_comment(cs_id: int, comment: str, cwd: Path) -> None:
    """cm changeset editcomment cs:<id> "<comment>" """
    run_cm(["changeset", "editcomment", f"cs:{cs_id}", comment], cwd=cwd)


def rollback_changeset(cs_id: int, cwd: Path) -> None:
    """Rollback workspace to before changeset cs_id. Uses cm undo --changeset."""
    run_cm(["undo", f"--changeset=cs:{cs_id}"], cwd=cwd)


def get_changesets(cwd: Path, limit: int = 10) -> list[Changeset]:
    """Return the most recent *limit* changesets, newest last.

    Uses: cm find changesets --format="{changesetid}|{date}|{owner}|{branch}|{comment}"
    Pipes the last *limit* lines via tail-equivalent slicing.
    """
    out = run_cm(["find", "changesets", f"--format={_FMT}"], cwd=cwd, safe=True)
    all_cs = parse_changesets(out)
    return all_cs[-limit:] if limit and len(all_cs) > limit else all_cs


def parse_changesets(output: str) -> list[Changeset]:
    results: list[Changeset] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on | — comment may contain | so cap at 4 splits
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        cs_id_str, date_str, owner, branch, comment = parts
        try:
            cs_id = int(cs_id_str.strip())
        except ValueError:
            continue
        results.append(Changeset(
            cs_id=cs_id,
            date=parse_date(date_str),
            owner=owner.strip(),
            branch=branch.strip(),
            comment=comment.strip(),
        ))
    return results
