"""Cached icon lookup by file extension."""

from __future__ import annotations

from functools import lru_cache

from biome_fm.qt import QApplication, QFileIconProvider, QFileInfo, QIcon, QStyle

_provider: QFileIconProvider | None = None


def _get_provider() -> QFileIconProvider:
    global _provider
    if _provider is None:
        _provider = QFileIconProvider()
    return _provider


@lru_cache(maxsize=256)
def icon_for_extension(ext: str) -> QIcon:
    """Cached icon by file extension. Falls back to SP_FileIcon."""
    if not ext:
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
    info = QFileInfo(f"dummy.{ext}")
    icon = _get_provider().icon(info)
    if icon.isNull():
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
    return icon


def icon_for_dir() -> QIcon:
    return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
