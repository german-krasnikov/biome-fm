"""Plastic SCM code review operations via cm codereview."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Review, parse_date

# title last so maxsplit=4 preserves pipe chars in title text
_REVIEW_FMT = "{id}|{status}|{assignee}|{date}|{title}"

REVIEW_STATUSES = ("Under review", "Reviewed", "Rework required")


def parse_reviews(output: str) -> list[Review]:
    results: list[Review] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        id_str, status, assignee, date_str, title = parts
        try:
            review_id = int(id_str.strip())
        except ValueError:
            continue
        results.append(Review(
            review_id=review_id,
            status=status.strip(),
            assignee=assignee.strip(),
            date=parse_date(date_str),
            title=title.strip(),
        ))
    return results


def create_review(cs_id: int, title: str, cwd: Path,
                  *, assignee: str = "", status: str = "Under review") -> None:
    args = ["codereview", f"cs:{cs_id}", title]
    if assignee:
        args.append(f"--assignee={assignee}")
    args.append(f"--status={status}")
    run_cm(args, cwd=cwd)


def edit_review_status(review_id: int, status: str, cwd: Path) -> None:
    run_cm(["codereview", "-e", str(review_id), f"--status={status}"], cwd=cwd)


def delete_review(review_id: int, cwd: Path) -> None:
    run_cm(["codereview", "-d", str(review_id)], cwd=cwd)
