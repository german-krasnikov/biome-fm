"""DnD MIME helpers — no dependency on any specific view widget."""
from __future__ import annotations

from biome_fm.qt import QMimeData, QUrl

_MIME = "application/x-biome-fm-paths"


def make_path_mime(paths: list[str], *, urls: bool = True) -> QMimeData:
    """Build QMimeData with biome-fm-paths + uri-list + text/plain."""
    mime = QMimeData()
    mime.setData(_MIME, "\n".join(paths).encode())
    if paths:
        if urls:
            mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
        mime.setText("\n".join(paths))
    return mime
