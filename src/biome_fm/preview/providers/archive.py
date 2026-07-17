"""Archive preview provider — lists zip/tar contents as HTML."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_ENTRIES = 500
_ZIP_EXTS = frozenset({".zip", ".jar", ".whl", ".egg"})
_TAR_EXTS = frozenset({".tar", ".tgz"})
_TAR_COMPOUND = {(".tar", ".gz"), (".tar", ".bz2"), (".tar", ".xz")}


class ArchivePreviewProvider:
    priority = 6

    def can_handle(self, path: Path) -> bool:
        sfx = path.suffix.lower()
        if sfx in _ZIP_EXTS or sfx in _TAR_EXTS:
            return True
        s = path.suffixes
        return len(s) >= 2 and tuple(s[-2:]) in _TAR_COMPOUND

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            return self._render_zip(req.path) if self._is_zip(req.path) else self._render_tar(req.path)
        except Exception as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

    def _is_zip(self, path: Path) -> bool:
        return path.suffix.lower() in _ZIP_EXTS

    def _render_zip(self, path: Path) -> PreviewResult:
        with zipfile.ZipFile(path) as zf:
            all_infos = zf.infolist()
            total = len(all_infos)
            total_size = sum(i.file_size for i in all_infos)
            infos = all_infos[:_MAX_ENTRIES]
        lines = [f"Archive: {path.name}  ({total} files, {_fmt(total_size)})", ""]
        for info in infos:
            size = _fmt(info.file_size) if not info.is_dir() else "DIR"
            lines.append(f"  {info.filename:<60s} {size:>10s}")
        if total > _MAX_ENTRIES:
            lines.append(f"\n... {total - _MAX_ENTRIES} more entries")
        return PreviewResult(kind=ContentKind.HTML, data=f"<pre>{''.join(l + chr(10) for l in lines)}</pre>")

    def _render_tar(self, path: Path) -> PreviewResult:
        with tarfile.open(path) as tf:
            members = tf.getmembers()
            total = len(members)
            total_size = sum(m.size for m in members if m.isfile())
            infos = members[:_MAX_ENTRIES]
        lines = [f"Archive: {path.name}  ({total} files, {_fmt(total_size)})", ""]
        for m in infos:
            size = _fmt(m.size) if m.isfile() else "DIR"
            lines.append(f"  {m.name:<60s} {size:>10s}")
        if total > _MAX_ENTRIES:
            lines.append(f"\n... {total - _MAX_ENTRIES} more entries")
        return PreviewResult(kind=ContentKind.HTML, data=f"<pre>{''.join(l + chr(10) for l in lines)}</pre>")


def _fmt(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} TB"
