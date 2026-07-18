from __future__ import annotations

from pathlib import Path

from biome_fm.models.bookmark_node import BookmarkNode


class Hotlist:
    def __init__(self, store) -> None:
        self._store = store

    def items(self, limit: int = 10) -> list[Path]:
        seen: set[Path] = set()
        result: list[Path] = []
        for entry in self._store.top(limit):
            if entry.path not in seen:
                seen.add(entry.path)
                result.append(entry.path)
        return result

    def grouped_items(self, bookmark_store=None, limit: int = 10) -> list[BookmarkNode]:
        """Return tree: Recent submenu (top-N frecency) + optional Bookmarks submenu."""
        recent_children = [
            BookmarkNode(kind="dir", path=p, name=p.name or str(p))
            for p in self.items(limit)
        ]
        result: list[BookmarkNode] = [
            BookmarkNode(kind="submenu", name="Recent", children=recent_children)
        ]
        if bookmark_store is not None:
            result.append(
                BookmarkNode(kind="submenu", name="Bookmarks", children=list(bookmark_store.tree()))
            )
        return result
