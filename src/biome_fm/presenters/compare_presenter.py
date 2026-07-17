"""ComparePresenter — Qt-free directory comparison logic."""

from __future__ import annotations

import difflib
import hashlib
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from biome_fm.models.file_item import FileItem

_MTIME_TOLERANCE = 1.0  # seconds

_SORT_ORDER: dict[CompareStatus, int] = {}  # populated after enum definition


class CompareStatus(Enum):
    EQUAL = "equal"
    LEFT_ONLY = "left_only"
    RIGHT_ONLY = "right_only"
    NEWER_LEFT = "newer_left"
    NEWER_RIGHT = "newer_right"
    DIFF_SIZE = "diff_size"


_SORT_ORDER.update({
    CompareStatus.LEFT_ONLY: 0,
    CompareStatus.RIGHT_ONLY: 1,
    CompareStatus.NEWER_LEFT: 2,
    CompareStatus.NEWER_RIGHT: 3,
    CompareStatus.DIFF_SIZE: 4,
    CompareStatus.EQUAL: 5,
})


@dataclass(frozen=True, slots=True)
class CompareEntry:
    name: str
    status: CompareStatus
    left: FileItem | None = None
    right: FileItem | None = None


def _compare_files(lf: FileItem, rf: FileItem) -> CompareStatus:
    if lf.size != rf.size:
        return CompareStatus.DIFF_SIZE
    diff = lf.modified - rf.modified
    if abs(diff) < _MTIME_TOLERANCE:
        return CompareStatus.EQUAL
    return CompareStatus.NEWER_LEFT if diff > 0 else CompareStatus.NEWER_RIGHT


class ComparePresenter:
    """Compares two directories. No Qt dependency."""

    def __init__(self, left_items: list[FileItem], right_items: list[FileItem]) -> None:
        self._left = {i.name: i for i in left_items}
        self._right = {i.name: i for i in right_items}
        self._result: list[CompareEntry] | None = None

    def compare(self) -> list[CompareEntry]:
        names = self._left.keys() | self._right.keys()
        entries = []
        for name in names:
            lf, rf = self._left.get(name), self._right.get(name)
            if lf is None:
                status = CompareStatus.RIGHT_ONLY
            elif rf is None:
                status = CompareStatus.LEFT_ONLY
            elif lf.is_dir and rf.is_dir:
                status = CompareStatus.EQUAL
            elif lf.is_dir != rf.is_dir:
                status = CompareStatus.DIFF_SIZE
            else:
                status = _compare_files(lf, rf)
            entries.append(CompareEntry(name=name, status=status, left=lf, right=rf))

        entries.sort(key=lambda e: (_SORT_ORDER[e.status], e.name.lower()))
        self._result = entries
        return entries

    def content_compare(self, left: Path, right: Path) -> list[CompareEntry]:
        """Compare dirs by file content (sha256 for <10 MB, size+mtime fallback)."""
        _MAX = 10 * 1024 * 1024

        def _digest(p: Path) -> str | None:
            try:
                if p.stat().st_size > _MAX:
                    return None
                return hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                return None

        lfiles = {f.name: f for f in left.iterdir() if f.is_file()}
        rfiles = {f.name: f for f in right.iterdir() if f.is_file()}
        entries: list[CompareEntry] = []
        for name in lfiles.keys() | rfiles.keys():
            lp, rp = lfiles.get(name), rfiles.get(name)
            if lp is None:
                st = rp.stat()  # type: ignore[union-attr]
                li, ri = None, FileItem(name=name, path=rp, is_dir=False, size=st.st_size, modified=st.st_mtime)  # type: ignore[arg-type]
                status = CompareStatus.RIGHT_ONLY
            elif rp is None:
                st = lp.stat()
                li, ri = FileItem(name=name, path=lp, is_dir=False, size=st.st_size, modified=st.st_mtime), None
                status = CompareStatus.LEFT_ONLY
            else:
                lst, rst = lp.stat(), rp.stat()
                li = FileItem(name=name, path=lp, is_dir=False, size=lst.st_size, modified=lst.st_mtime)
                ri = FileItem(name=name, path=rp, is_dir=False, size=rst.st_size, modified=rst.st_mtime)
                ld, rd = _digest(lp), _digest(rp)
                if ld is not None and rd is not None:
                    status = CompareStatus.EQUAL if ld == rd else CompareStatus.DIFF_SIZE
                else:
                    status = _compare_files(li, ri)
            entries.append(CompareEntry(name=name, status=status, left=li, right=ri))
        entries.sort(key=lambda e: (_SORT_ORDER[e.status], e.name.lower()))
        return entries

    @staticmethod
    def content_diff(entry: CompareEntry, context_lines: int = 3) -> str:
        """Return unified diff string for two files. Returns '' if equal/binary/missing side."""
        if entry.left is None or entry.right is None:
            return ""
        _MAX = 512 * 1024
        try:
            lb = entry.left.path.read_bytes()
            rb = entry.right.path.read_bytes()
        except OSError:
            return ""
        for data in (lb[:8192], rb[:8192]):
            if b"\x00" in data:
                return "(binary files differ)"
        la = lb[:_MAX].decode("utf-8", errors="replace").splitlines(keepends=True)
        ra = rb[:_MAX].decode("utf-8", errors="replace").splitlines(keepends=True)
        lines = list(difflib.unified_diff(
            la, ra,
            fromfile=str(entry.left.path),
            tofile=str(entry.right.path),
            n=context_lines,
        ))
        return "".join(lines)

    @property
    def summary(self) -> str:
        if self._result is None:
            self.compare()
        counts = Counter(e.status for e in self._result)  # type: ignore[union-attr]
        labels = {
            CompareStatus.EQUAL: "equal",
            CompareStatus.LEFT_ONLY: "left only",
            CompareStatus.RIGHT_ONLY: "right only",
            CompareStatus.NEWER_LEFT: "newer left",
            CompareStatus.NEWER_RIGHT: "newer right",
            CompareStatus.DIFF_SIZE: "diff size",
        }
        parts = [f"{counts[s]} {labels[s]}" for s in CompareStatus if counts[s]]
        return ", ".join(parts)
