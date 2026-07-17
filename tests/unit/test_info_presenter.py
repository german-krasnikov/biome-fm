"""Tests for InfoPresenter — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.info_presenter import InfoPresenter


class _MockInfoView:
    def __init__(self):
        self.cleared = False
        self.updates: list[dict] = []

    def clear(self) -> None:
        self.cleared = True
        self.updates.clear()

    def update_fields(self, fields: dict) -> None:
        self.updates.append(fields)


def _file(name="file.txt", size=1024, mtime=1234567890.0, perms="rw-r--r--"):
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False,
                    size=size, modified=mtime, permissions=perms)


def _dir(name="mydir"):
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=True,
                    size=0, modified=0.0)


def test_none_item_clears():
    view = _MockInfoView()
    p = InfoPresenter(view)
    p.on_cursor_changed(None)
    assert view.cleared


def test_file_shows_size_mtime():
    view = _MockInfoView()
    p = InfoPresenter(view)
    item = _file(size=2048)
    p.on_cursor_changed(item)
    assert view.updates
    fields = view.updates[-1]
    assert "size" in fields
    assert "2048" in fields["size"] or "2" in fields["size"]  # size or human-readable
    assert "mtime" in fields


def test_dir_shows_no_size():
    view = _MockInfoView()
    p = InfoPresenter(view)
    p.on_cursor_changed(_dir())
    assert view.updates
    fields = view.updates[-1]
    # directories show <DIR> or no size
    size_val = fields.get("size", "")
    assert "DIR" in size_val or size_val == ""
