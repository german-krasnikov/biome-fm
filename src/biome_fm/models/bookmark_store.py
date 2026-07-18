"""TOML-backed bookmark tree. Supports dirs, submenus, and separators."""
from __future__ import annotations

import copy
import os
import tomllib
from pathlib import Path

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.models.bookmark_node import display_label as _node_label

# ── helpers ───────────────────────────────────────────────────────────────────

def _build_tree(flat: list[dict]) -> list[BookmarkNode]:
    """Flat [{kind, path?, name?, depth?}] → tree."""
    root: list[BookmarkNode] = []
    stack: list[tuple[int, list[BookmarkNode]]] = [(-1, root)]
    for item in flat:
        d = item.get("depth", 0)
        while stack[-1][0] >= d:
            stack.pop()
        node = BookmarkNode(
            kind=item["kind"],
            path=Path(item["path"]) if item.get("path") else None,
            name=item.get("name", ""),
        )
        stack[-1][1].append(node)
        if node.kind == "submenu":
            stack.append((d, node.children))
    return root


def _flatten_nodes(nodes: list[BookmarkNode], depth: int = 0) -> list[dict]:
    result: list[dict] = []
    for n in nodes:
        d: dict = {"kind": n.kind}
        if n.path:
            d["path"] = str(n.path)
        if n.name:
            d["name"] = n.name
        if depth:
            d["depth"] = depth
        result.append(d)
        if n.kind == "submenu":
            result.extend(_flatten_nodes(n.children, depth + 1))
    return result


def _find_dir(nodes: list[BookmarkNode], path: Path) -> BookmarkNode | None:
    for n in nodes:
        if n.kind == "dir" and n.path == path:
            return n
        if n.kind == "submenu":
            found = _find_dir(n.children, path)
            if found:
                return found
    return None


def _collect_dirs(nodes: list[BookmarkNode]) -> list[Path]:
    result: list[Path] = []
    for n in nodes:
        if n.kind == "dir" and n.path:
            result.append(n.path)
        if n.kind == "submenu":
            result.extend(_collect_dirs(n.children))
    return result


def _remove_from_tree(nodes: list[BookmarkNode], path: Path) -> bool:
    for i, n in enumerate(nodes):
        if n.kind == "dir" and n.path == path:
            nodes.pop(i)
            return True
        if n.kind == "submenu" and _remove_from_tree(n.children, path):
            return True
    return False


def _migrate_old(bm: dict) -> list[BookmarkNode]:
    """Convert old flat paths/names + optional [[bookmarks.groups]] to tree."""
    paths_raw: list[str] = bm.get("paths", [])
    names_raw: list[str] = bm.get("names", [])

    nodes: list[BookmarkNode] = []
    # Pass 1: build flat list, detect dash-prefix children
    flat: list[tuple[Path, str]] = []
    for i, ps in enumerate(paths_raw):
        name = names_raw[i] if i < len(names_raw) else ""
        flat.append((Path(ps), name))

    # Group consecutive dash-prefix items under the preceding plain item
    i = 0
    while i < len(flat):
        p, name = flat[i]
        if name.startswith("- "):
            # orphan child with no parent — add as plain dir
            nodes.append(BookmarkNode("dir", p, name[2:]))
            i += 1
            continue
        # look ahead for dash-prefix children
        children: list[BookmarkNode] = []
        j = i + 1
        while j < len(flat) and flat[j][1].startswith("- "):
            cp, cn = flat[j]
            children.append(BookmarkNode("dir", cp, cn[2:]))
            j += 1
        if children:
            # turn the parent into a submenu, keep a dir node for it too
            sub = BookmarkNode("submenu", name=name or p.name or str(p))
            sub.children.append(BookmarkNode("dir", p, name))
            sub.children.extend(children)
            nodes.append(sub)
        else:
            nodes.append(BookmarkNode("dir", p, name))
        i = j if children else i + 1

    # Pass 2: old [[bookmarks.groups]]
    for grp in bm.get("groups", []):
        try:
            gname = grp.get("name", "Group")
            gpaths = [Path(s) for s in grp.get("paths", [])]
            gnraw: list[str] = grp.get("names", [])
            sub = BookmarkNode("submenu", name=gname)
            existing = _collect_dirs(nodes)
            for k, gp in enumerate(gpaths):
                if gp in existing:
                    continue
                gn = gnraw[k] if k < len(gnraw) and gnraw[k] else ""
                sub.children.append(BookmarkNode("dir", gp, gn))
            if sub.children:
                nodes.append(sub)
        except (KeyError, TypeError):
            continue

    return nodes


# ── BookmarkStore ─────────────────────────────────────────────────────────────

class BookmarkStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._nodes: list[BookmarkNode] = []
        self._numbered: dict[int, Path] = {}
        self._load()

    # ── numbered slots (Ctrl+1–9) ─────────────────────────────────────────────

    def set_numbered(self, slot: int, path: Path) -> None:
        if slot not in range(1, 10):
            raise ValueError(f"slot must be 1-9, got {slot}")
        self._numbered[slot] = path

    def get_numbered(self, slot: int) -> Path | None:
        return self._numbered.get(slot)

    def clear_numbered(self, slot: int) -> None:
        self._numbered.pop(slot, None)

    # ── tree API ──────────────────────────────────────────────────────────────

    def tree(self) -> list[BookmarkNode]:
        return copy.deepcopy(self._nodes)

    def set_tree(self, nodes: list[BookmarkNode]) -> None:
        self._nodes = copy.deepcopy(nodes)
        self._save()

    # ── flat compat API ───────────────────────────────────────────────────────

    def add(self, path: Path, name: str = "") -> None:
        if path in self:
            return
        self._nodes.append(BookmarkNode("dir", path, name))
        self._save()

    def remove(self, path: Path) -> None:
        _remove_from_tree(self._nodes, path)
        self._save()

    def __contains__(self, path: Path) -> bool:
        return _find_dir(self._nodes, path) is not None

    def all(self) -> list[Path]:
        return _collect_dirs(self._nodes)

    def get_name(self, path: Path) -> str:
        n = _find_dir(self._nodes, path)
        return n.name if n else ""

    def set_name(self, path: Path, name: str) -> None:
        n = _find_dir(self._nodes, path)
        if n is None:
            return
        n.name = name
        self._save()

    def display_label(self, path: Path) -> str:
        n = _find_dir(self._nodes, path)
        if n is None:
            return path.name or str(path)
        return _node_label(n)

    # ── persistence ───────────────────────────────────────────────────────────

    @staticmethod
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

    def _save(self) -> None:
        flat = _flatten_nodes(self._nodes)
        e = self._esc
        lines: list[str] = []
        for item in flat:
            lines.append("\n[[bookmarks.items]]")
            lines.append(f'kind = "{item["kind"]}"')
            if "path" in item:
                lines.append(f'path = "{e(item["path"])}"')
            if "name" in item:
                lines.append(f'name = "{e(item["name"])}"')
            if "depth" in item:
                lines.append(f'depth = {item["depth"]}')
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, self._path)

    def _load(self) -> None:
        if not self._path.exists():
            self._nodes = [
                BookmarkNode("dir", p)
                for p in self._default_paths()
                if p.is_dir()
            ]
            if self._nodes:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._save()
            return
        try:
            data = tomllib.loads(self._path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            self._nodes = []
            return
        bm = data.get("bookmarks", {})
        if not isinstance(bm, dict):
            self._nodes = []
            return
        if "items" in bm:
            self._nodes = _build_tree(bm["items"])
        else:
            self._nodes = _migrate_old(bm)
            self._save()

    @staticmethod
    def _default_paths() -> list[Path]:
        home = Path.home()
        return [home, home / "Desktop", home / "Documents", home / "Downloads"]
