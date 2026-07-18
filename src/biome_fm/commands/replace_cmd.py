"""ReplaceCmd — in-place text replacement with backup + undo (F023)."""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.presenters.search_presenter import _decode_content


@dataclass
class ReplaceResult:
    path: Path
    count: int
    preview: str  # first replaced line (up to 200 chars)


def _apply(text: str, pattern: re.Pattern[str], replacement: str) -> tuple[int, str, str]:
    """Returns (count, new_text, preview_line). count=0 → no-op."""
    count = len(pattern.findall(text))
    if not count:
        return 0, text, ""
    new_text = pattern.sub(replacement, text)
    preview = next((ln[:200] for ln in new_text.splitlines() if replacement in ln), "")
    return count, new_text, preview


class ReplaceCmd(Command):
    undoable = True

    def __init__(self, path: Path, query: str, replacement: str, regex: bool = False) -> None:
        self._path = path
        self._replacement = replacement
        self._bak = path.with_suffix(path.suffix + ".bak")
        flags = re.DOTALL  # sensible default; callers can pass compiled pattern if needed
        self._pattern = re.compile(query if regex else re.escape(query), flags)

    def execute(self) -> ReplaceResult:  # type: ignore[override]
        raw = self._path.read_bytes()
        text = _decode_content(raw)
        if text is None:
            return ReplaceResult(self._path, 0, "")
        count, new_text, preview = _apply(text, self._pattern, self._replacement)
        if not count:
            return ReplaceResult(self._path, 0, "")
        shutil.copy2(self._path, self._bak)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        tmp.rename(self._path)
        return ReplaceResult(self._path, count, preview)

    def undo(self) -> None:
        if self._bak.exists():
            self._bak.replace(self._path)  # atomic on same FS; removes .bak


def search_replace(
    paths: list[Path],
    query: str,
    replacement: str,
    regex: bool = False,
    dry_run: bool = False,
) -> list[ReplaceResult]:
    """Replace query in multiple files. Skips binary files and zero-match files."""
    pattern = re.compile(query if regex else re.escape(query), re.DOTALL)
    results: list[ReplaceResult] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        text = _decode_content(raw)
        if text is None:
            continue
        count, new_text, preview = _apply(text, pattern, replacement)
        if not count:
            continue
        if not dry_run:
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(new_text, encoding="utf-8")
            tmp.rename(path)
        results.append(ReplaceResult(path, count, preview))
    return results
