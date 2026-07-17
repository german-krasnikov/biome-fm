"""Copy command — copy to dest dir (undoable via delete)."""
from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.conflict_resolver import ConflictAction, ConflictResolver, auto_rename
from biome_fm.models.vfs import VFSProtocol
from biome_fm.operations.task import Cancelled


class CopyCmd(Command):
    def __init__(self, sources: list[Path], dest_dir: Path, vfs: VFSProtocol) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._created: list[Path] = []

    def execute(self) -> None:
        self._created.clear()
        for src in self._sources:
            dst = self._dest_dir / src.name
            self._vfs.copy(src, dst)
            self._created.append(dst)

    def undo(self) -> None:
        for p in reversed(self._created):
            self._vfs.delete(p)
        self._created.clear()

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Copy {n} item{'s' if n != 1 else ''}"


class ProgressCopyCmd(Command):
    """Chunk-based copy with per-byte progress reporting and cancel support."""

    CHUNK = 256 * 1024

    def __init__(
        self,
        sources: list[Path],
        dest_dir: Path,
        vfs: object,  # unused — kept for API symmetry with CopyCmd
        cancel: object,  # threading.Event
        report: Callable[..., None],
        chunk: int | None = None,
        conflict_resolver: ConflictResolver | None = None,
        verify: bool = False,
    ) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._cancel = cancel
        self._report = report
        self._chunk = chunk or self.CHUNK
        self._resolver = conflict_resolver
        self._verify = verify
        self._created: list[Path] = []

    def execute(self) -> None:
        self._created.clear()
        total = len(self._sources)
        for i, src in enumerate(self._sources):
            if self._cancel.is_set():
                raise Cancelled()
            dst = self._dest_dir / src.name
            if dst.exists() and self._resolver is not None:
                action = self._resolver.ask(src, dst)
                if action in (ConflictAction.SKIP, ConflictAction.SKIP_ALL):
                    continue
                if action == ConflictAction.CANCEL:
                    raise Cancelled()
                if action == ConflictAction.RENAME:
                    dst = auto_rename(dst)
                # OVERWRITE / OVERWRITE_ALL fall through
            if src.is_dir():
                try:
                    self._copy_dir(src, dst)
                except Exception:
                    shutil.rmtree(dst, ignore_errors=True)
                    raise
            else:
                self._copy_file(src, dst, i, total)
            self._created.append(dst)

    def _copy_dir(self, src: Path, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            if self._cancel.is_set():
                raise Cancelled()
            if child.is_dir():
                self._copy_dir(child, dst / child.name)
            else:
                self._copy_file(child, dst / child.name)
        shutil.copystat(src, dst)

    def _copy_file(self, src: Path, dst: Path, files_done: int = 0, files_total: int = 0) -> None:
        size = src.stat().st_size
        done = 0
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            while data := fin.read(self._chunk):
                if self._cancel.is_set():
                    fout.close()
                    dst.unlink(missing_ok=True)
                    raise Cancelled()
                fout.write(data)
                done += len(data)
                self._report(files_done, files_total, done, size, src.name)
        shutil.copystat(src, dst)
        self._report(files_done + 1, files_total, size, size, src.name)
        if self._verify:
            self._verify_file(src, dst)

    def _verify_file(self, src: Path, dst: Path) -> None:
        import hashlib

        def _hash(p: Path) -> bytes:
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.digest()

        if _hash(src) != _hash(dst):
            raise RuntimeError(f"Checksum mismatch: {src.name}")

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
        return f"Copy {n} item{'s' if n != 1 else ''}"
