"""Pure-Python git merge conflict detection and parsing — no Qt."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_TIMEOUT = 5


@dataclass(frozen=True)
class ConflictMarker:
    line: int       # 1-indexed
    marker: str     # "<<<<<<<", "=======", or ">>>>>>>"
    label: str      # text after the marker, stripped


@dataclass
class ConflictRegion:
    start: int              # line number of <<<<<<<
    separator: int          # line number of =======
    end: int                # line number of >>>>>>>
    ours: list[str] = field(default_factory=list)
    theirs: list[str] = field(default_factory=list)


def conflicted_files(repo: Path) -> list[str]:
    """Return list of unmerged file paths relative to repo root."""
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return [line for line in r.stdout.splitlines() if line]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []


def find_conflict_markers(file_path: Path) -> list[ConflictMarker]:
    """Return all conflict marker lines in file. Empty on binary/missing/clean."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    result: list[ConflictMarker] = []
    for i, line in enumerate(lines, start=1):
        if line.startswith("<<<<<<<"):
            result.append(ConflictMarker(i, "<<<<<<<", line[7:].strip()))
        elif line.startswith("======="):
            result.append(ConflictMarker(i, "=======", line[7:].strip()))
        elif line.startswith(">>>>>>>"):
            result.append(ConflictMarker(i, ">>>>>>>", line[7:].strip()))
    return result


def parse_conflict_regions(file_path: Path) -> list[ConflictRegion]:
    """Extract full conflict regions (ours/theirs content) from file."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    regions: list[ConflictRegion] = []
    region: ConflictRegion | None = None

    for i, line in enumerate(lines, start=1):
        if line.startswith("<<<<<<<"):
            region = ConflictRegion(start=i, separator=0, end=0)
        elif line.startswith("=======") and region and region.separator == 0:
            region.separator = i
        elif line.startswith(">>>>>>>") and region and region.separator:
            region.end = i
            regions.append(region)
            region = None
        elif region:
            if region.separator == 0:
                region.ours.append(line)
            else:
                region.theirs.append(line)

    return regions
