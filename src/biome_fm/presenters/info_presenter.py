"""InfoPresenter — updates the InfoPanel with file metadata."""
from __future__ import annotations

import datetime
import mimetypes
from typing import Protocol

from biome_fm.models.file_item import FileItem


class InfoViewProtocol(Protocol):
    def clear(self) -> None: ...
    def update_fields(self, fields: dict) -> None: ...


class InfoPresenter:
    def __init__(self, view: InfoViewProtocol) -> None:
        self._view = view

    def on_cursor_changed(self, item: FileItem | None) -> None:
        if item is None:
            self._view.clear()
            return
        mtime_str = datetime.datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M:%S")
        mime, _ = mimetypes.guess_type(item.name)
        fields = {
            "name": item.name,
            "size": item.size_str,
            "mtime": mtime_str,
            "permissions": item.permissions or "—",
            "mime": mime or "—",
        }
        self._view.update_fields(fields)
