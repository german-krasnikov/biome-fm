"""Batch execute shell template on each selected file."""
from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command

_EXPANSION = {
    "{f}": lambda p: str(p),
    "{n}": lambda p: p.stem,
    "{e}": lambda p: p.suffix.lstrip("."),
    "{d}": lambda p: str(p.parent),
}


def expand_template(template: str, path: Path) -> str:
    for token, fn in _EXPANSION.items():
        template = template.replace(token, fn(path))
    return template


class BatchExecCmd(Command):
    undoable = False

    def __init__(
        self,
        template: str,
        paths: list[Path],
        cancel: threading.Event | None = None,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> None:
        self._template = template
        self._paths = paths
        self._cancel = cancel or threading.Event()
        self._on_progress = on_progress

    @property
    def description(self) -> str:
        return f"Batch exec '{self._template}' on {len(self._paths)} files"

    def execute(self) -> None:
        for i, path in enumerate(self._paths):
            if self._cancel.is_set():
                break
            cmd = expand_template(self._template, path)
            if self._on_progress:
                self._on_progress(i, len(self._paths), cmd)
            subprocess.run(cmd, shell=True, check=False)

    def undo(self) -> None:
        pass
