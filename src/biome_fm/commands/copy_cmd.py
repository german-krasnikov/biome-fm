"""Copy command — copy to dest dir."""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.conflict_resolver import (
    ConflictAction,
    ConflictResolver,
    PreCopyConflictResolver,
    auto_rename,
)
from biome_fm.models.vfs import VFSProtocol
from biome_fm.operations.task import Cancelled

_ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_RESERVED = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$', re.IGNORECASE)


def _check_filename_safety(name: str) -> str | None:
    """Return sanitized name if *name* contains illegal chars or is a reserved Windows name, else None."""
    sanitized = _ILLEGAL.sub('_', name)
    changed = sanitized != name
    stem = Path(sanitized).stem
    if _RESERVED.match(stem):
        sanitized = '_' + sanitized
        changed = True
    return sanitized if changed else None


class CopyCmd(Command):
    def __init__(self, sources: list[Path], dest_dir: Path, vfs: VFSProtocol) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs

    def execute(self) -> None:
        for src in self._sources:
            dst = self._dest_dir / src.name
            self._vfs.copy(src, dst)

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Copy {n} item{'s' if n != 1 else ''}"

    def preview(self) -> list[str]:
        return [f"Copy {s.name}  →  {self._dest_dir / s.name}" for s in self._sources]


class ProgressCopyCmd(Command):
    """Chunk-based copy with per-byte progress reporting and cancel support."""

    CHUNK = 256 * 1024

    def __init__(
        self,
        sources: list[Path],
        dest_dir: Path,
        vfs: object,
        cancel: object,  # threading.Event
        report: Callable[..., None],
        chunk: int | None = None,
        conflict_resolver: ConflictResolver | None = None,
        verify: bool = False,
        strategy: ConflictAction | None = None,
        pause: object = None,  # threading.Event; SET = running, CLEAR = paused
        src_vfs: object = None,  # source VFS for cross-VFS reads; None = local fs
    ) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._cancel = cancel
        self._report = report
        self._chunk = chunk or self.CHUNK
        self._resolver = (
            PreCopyConflictResolver(strategy) if strategy is not None else conflict_resolver
        )
        self._verify = verify
        self._pause = pause
        self._src_vfs = src_vfs
        self._backups: dict[Path, Path] = {}  # dst -> temp backup; only for overwrites
        self._pre_existed_dirs: dict[Path, bool] = {}  # dst dir -> pre-existed before execute()

    def _save_backup(self, dst: Path) -> Path:
        """Copy dst to a sibling temp file on the same filesystem (atomic rename on restore)."""
        fd, tmp = tempfile.mkstemp(dir=dst.parent, prefix=".biome_bak_", suffix=".tmp")
        os.close(fd)
        try:
            shutil.copy2(dst, tmp)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise
        return Path(tmp)

    def execute(self) -> None:
        for bak in self._backups.values():
            bak.unlink(missing_ok=True)
        self._backups.clear()
        self._pre_existed_dirs.clear()
        total = len(self._sources)
        for i, src in enumerate(self._sources):
            if self._cancel.is_set():
                raise Cancelled()
            dst = self._dest_dir / src.name
            force_overwrite = False
            if dst.exists() and self._resolver is not None:
                action = self._resolver.ask(src, dst)
                if action in (ConflictAction.SKIP, ConflictAction.SKIP_ALL):
                    continue
                if action == ConflictAction.CANCEL:
                    raise Cancelled()
                if action == ConflictAction.RENAME:
                    dst = auto_rename(dst)
                elif action in (ConflictAction.OVERWRITE, ConflictAction.OVERWRITE_ALL):
                    force_overwrite = True
            pre_existed = dst.exists()
            self._pre_existed_dirs[dst] = pre_existed
            if src.is_dir():
                try:
                    self._copy_dir(src, dst, force_overwrite)
                except Exception:
                    if not pre_existed:
                        shutil.rmtree(dst, ignore_errors=True)
                    raise
            elif src.is_file():
                backup = None
                if force_overwrite and dst.exists():
                    backup = self._save_backup(dst)
                    self._backups[dst] = backup
                try:
                    self._copy_file(src, dst, i, total, force_overwrite=force_overwrite)
                except Exception:
                    if backup is not None:
                        try:
                            shutil.move(str(backup), str(dst))
                        except Exception:
                            pass
                        self._backups.pop(dst, None)
                    raise
            elif self._src_vfs is not None:
                # Cross-VFS: read from src_vfs, write locally
                self._copy_cross_vfs(src, dst, i, total, force_overwrite)
            elif self._vfs is not None:
                # Archive path — ask the VFS
                try:
                    stat = self._vfs.stat(src)
                    is_dir = stat.is_dir
                except Exception:
                    is_dir = False
                if is_dir:
                    try:
                        self._copy_archive_dir(src, dst)
                    except Exception:
                        shutil.rmtree(dst, ignore_errors=True)
                        raise
                else:
                    self._copy_archive_file(src, dst, i, total)

    def _copy_dir(self, src: Path, dst: Path, force_overwrite: bool = False) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            if self._cancel.is_set():
                raise Cancelled()
            if _check_filename_safety(child.name) is not None:
                raise ValueError(f"Illegal filename: {child.name}")
            if child.is_dir():
                child_dst = dst / child.name
                self._pre_existed_dirs.setdefault(child_dst, child_dst.exists())
                self._copy_dir(child, child_dst, force_overwrite)
            else:
                leaf_dst = dst / child.name
                self._copy_file(child, leaf_dst, force_overwrite=force_overwrite)
        shutil.copystat(src, dst)

    def _copy_archive_dir(self, src: Path, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        for item in self._vfs.listdir(src):
            if self._cancel.is_set():
                raise Cancelled()
            if item.is_dir:
                self._copy_archive_dir(item.path, dst / item.name)
            else:
                self._copy_archive_file(item.path, dst / item.name)

    def _copy_cross_vfs(self, src: Path, dst: Path, files_done: int = 0, files_total: int = 0, force_overwrite: bool = False) -> None:
        import os
        dst.parent.mkdir(parents=True, exist_ok=True)
        offset = 0
        if not force_overwrite and dst.exists() and hasattr(self._src_vfs, "open_read") and hasattr(self._src_vfs, "stat"):
            try:
                remote_size = self._src_vfs.stat(src).size
                local_size = dst.stat().st_size
                if 0 < local_size < remote_size:
                    offset = local_size
            except Exception:
                pass
        if hasattr(self._src_vfs, "open_read"):
            mode = "ab" if offset else "wb"
            done = offset
            with self._src_vfs.open_read(src, offset=offset) as fin, open(dst, mode) as fout:
                while data := fin.read(self._chunk):
                    if self._cancel.is_set():
                        raise Cancelled()
                    fout.write(data)
                    done += len(data)
                    self._report(files_done, files_total, done, 0, src.name)
        else:
            raw = self._src_vfs.read_bytes(src)  # type: ignore[union-attr]
            if self._cancel.is_set():
                raise Cancelled()
            dst.write_bytes(raw)
            done = len(raw)
        if hasattr(self._src_vfs, "stat"):
            try:
                fi = self._src_vfs.stat(src)
                if fi.modified:
                    os.utime(dst, (fi.modified, fi.modified))
            except Exception:
                pass
        self._report(files_done + 1, files_total, done, done, src.name)

    def _copy_archive_file(self, src: Path, dst: Path, files_done: int = 0, files_total: int = 0) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        done = 0
        with self._vfs.open_file(src) as fin, open(dst, "wb") as fout:
            while data := fin.read(self._chunk):
                self._wait_if_paused(fout, dst)
                if self._cancel.is_set():
                    fout.close()
                    dst.unlink(missing_ok=True)
                    raise Cancelled()
                fout.write(data)
                done += len(data)
                self._report(files_done, files_total, done, 0, src.name)

    def _copy_file(
        self, src: Path, dst: Path,
        files_done: int = 0, files_total: int = 0,
        force_overwrite: bool = False,
    ) -> None:
        try:
            if dst.exists() and os.path.samefile(src, dst):
                raise shutil.SameFileError(str(src))
        except FileNotFoundError:
            pass
        size = src.stat().st_size
        offset = 0
        mode = "wb"
        if (
            not force_overwrite
            and dst.exists()
            and (dst_size := dst.stat().st_size) < size
            and dst.stat().st_mtime >= src.stat().st_mtime
        ):
            offset = dst_size
            mode = "ab"
        done = offset
        with open(src, "rb") as fin, open(dst, mode) as fout:
            if offset:
                fin.seek(offset)
            while data := fin.read(self._chunk):
                self._wait_if_paused(fout, dst)
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

    def _wait_if_paused(self, fout: object, dst: Path) -> None:
        if self._pause is None:
            return
        while not self._pause.wait(timeout=0.05):
            if self._cancel.is_set():
                return  # let the caller handle cancel

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

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Copy {n} item{'s' if n != 1 else ''}"
