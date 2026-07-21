"""RsyncCmd — delta-transfer via rsync subprocess."""
from __future__ import annotations

import shutil
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.operations.task import Cancelled


def rsync_available() -> bool:
    return shutil.which("rsync") is not None


class RsyncCmd(Command):
    """Copy sources to dest_dir using rsync (delta-transfer, resume)."""

    def __init__(
        self,
        sources: list[Path],
        dest_dir: Path,
        cancel: threading.Event,
        report: Callable[..., None],
        extra_args: list[str] | None = None,
    ) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._cancel = cancel
        self._report = report
        self._extra_args = extra_args or []
        self._created: list[Path] = []

    def execute(self) -> None:
        if not rsync_available():
            raise RuntimeError("rsync not found in PATH")
        self._created.clear()
        args = [
            "rsync", "--partial", "--archive", "--progress",
            "--human-readable",
            *self._extra_args,
            *[str(s) for s in self._sources],
            str(self._dest_dir) + "/",
        ]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in proc.stdout:  # type: ignore[union-attr]
            if self._cancel.is_set():
                proc.terminate()
                raise Cancelled()
            line = line.rstrip()
            if "%" in line:
                parts = line.split()
                if len(parts) >= 2 and "%" in parts[1]:
                    try:
                        pct = int(parts[1].rstrip("%"))
                        self._report(0, len(self._sources), pct, 100, "")
                    except (ValueError, IndexError):
                        pass
        proc.wait()
        if proc.returncode not in (0, 24):  # 24 = partial transfer (files vanished)
            raise OSError(f"rsync failed with code {proc.returncode}")
        for src in self._sources:
            self._created.append(self._dest_dir / src.name)

    def undo(self) -> None:
        for p in reversed(self._created):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        self._created.clear()

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Rsync {n} item{'s' if n != 1 else ''}"
