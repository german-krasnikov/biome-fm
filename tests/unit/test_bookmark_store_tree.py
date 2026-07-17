"""Tree API tests for BookmarkStore. No Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.models.bookmark_store import BookmarkStore


@pytest.fixture
def store(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text("[bookmarks]\npaths = []\n")
    return BookmarkStore(p)


# ── Cycle A: tree basics ──────────────────────────────────────────────────────

def test_tree_returns_root_nodes(tmp_path):
    """Fresh store (missing file) → default dirs at root level."""
    s = BookmarkStore(tmp_path / "fresh.toml")
    t = s.tree()
    assert isinstance(t, list)
    assert all(isinstance(n, BookmarkNode) for n in t)
    # at least one default dir exists
    kinds = {n.kind for n in t}
    assert "dir" in kinds


def test_set_tree_persists(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    nodes = [
        BookmarkNode("dir", Path("/a"), "Alpha"),
        BookmarkNode("dir", Path("/b")),
    ]
    s1.set_tree(nodes)
    s2 = BookmarkStore(p)
    t = s2.tree()
    assert len(t) == 2
    assert t[0].path == Path("/a")
    assert t[0].name == "Alpha"
    assert t[1].path == Path("/b")


def test_set_tree_with_submenu(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    child = BookmarkNode("dir", Path("/work/proj"), "Proj")
    sub = BookmarkNode("submenu", name="Work", children=[child])
    s1.set_tree([BookmarkNode("dir", Path("/a")), sub])
    s2 = BookmarkStore(p)
    t = s2.tree()
    assert len(t) == 2
    assert t[1].kind == "submenu"
    assert t[1].name == "Work"
    assert len(t[1].children) == 1
    assert t[1].children[0].path == Path("/work/proj")


def test_set_tree_with_separator(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    s1.set_tree([
        BookmarkNode("dir", Path("/a")),
        BookmarkNode("separator"),
        BookmarkNode("dir", Path("/b")),
    ])
    s2 = BookmarkStore(p)
    t = s2.tree()
    assert t[1].kind == "separator"
    assert t[2].path == Path("/b")


# ── Cycle B: flat compat API ──────────────────────────────────────────────────

def test_add_appends_dir_at_root(store):
    store.add(Path("/new/dir"))
    t = store.tree()
    paths = [n.path for n in t if n.kind == "dir"]
    assert Path("/new/dir") in paths


def test_add_dedup(store):
    store.add(Path("/dup"))
    store.add(Path("/dup"))
    paths = [n.path for n in store.tree() if n.kind == "dir"]
    assert paths.count(Path("/dup")) == 1


def test_remove_from_root(store):
    store.add(Path("/a"))
    store.remove(Path("/a"))
    assert Path("/a") not in store


def test_remove_from_submenu(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    child = BookmarkNode("dir", Path("/nested"), "Nested")
    sub = BookmarkNode("submenu", name="Grp", children=[child])
    s.set_tree([sub])
    s.remove(Path("/nested"))
    assert Path("/nested") not in s


def test_contains_root(store):
    store.add(Path("/check"))
    assert Path("/check") in store


def test_contains_nested(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    child = BookmarkNode("dir", Path("/deep"), "Deep")
    sub = BookmarkNode("submenu", name="G", children=[child])
    s.set_tree([sub])
    assert Path("/deep") in s


def test_contains_missing(store):
    assert Path("/nowhere") not in store


def test_all_returns_flat_dirs(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    child = BookmarkNode("dir", Path("/b"), "B")
    sub = BookmarkNode("submenu", name="S", children=[child])
    s.set_tree([BookmarkNode("dir", Path("/a")), sub, BookmarkNode("dir", Path("/c"))])
    assert s.all() == [Path("/a"), Path("/b"), Path("/c")]


def test_display_label_custom_name(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    s.set_tree([BookmarkNode("dir", Path("/x"), "MyLabel")])
    assert s.display_label(Path("/x")) == "MyLabel"


def test_display_label_no_name(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    s.set_tree([BookmarkNode("dir", Path("/x/mydir"))])
    assert s.display_label(Path("/x/mydir")) == "mydir"


# ── Cycle C: TOML persistence ─────────────────────────────────────────────────

def test_toml_roundtrip_nested(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    inner = BookmarkNode("dir", Path("/inner"), "Inner")
    outer_sub = BookmarkNode("submenu", name="Outer", children=[
        BookmarkNode("submenu", name="Inner Group", children=[inner])
    ])
    s1.set_tree([outer_sub])
    s2 = BookmarkStore(p)
    t = s2.tree()
    assert t[0].kind == "submenu"
    assert t[0].name == "Outer"
    nested = t[0].children[0]
    assert nested.kind == "submenu"
    assert nested.name == "Inner Group"
    assert nested.children[0].path == Path("/inner")


def test_toml_no_depth_for_root(tmp_path):
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    s.set_tree([BookmarkNode("dir", Path("/a"))])
    content = p.read_text()
    # Root items must not have a depth field
    assert "depth" not in content


def test_corrupt_toml_no_crash(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text("!!! invalid {{{{")
    s = BookmarkStore(p)
    assert s.all() == []


# ── Cycle D: migration ────────────────────────────────────────────────────────

def test_migrate_old_flat_format(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text('[bookmarks]\npaths = ["/a", "/b"]\nnames = ["", ""]\n')
    s = BookmarkStore(p)
    assert s.all() == [Path("/a"), Path("/b")]


def test_migrate_dash_prefix(tmp_path):
    """Old dash-prefix names become submenu children."""
    p = tmp_path / "bm.toml"
    p.write_text(
        '[bookmarks]\n'
        'paths = ["/root", "/child1", "/child2"]\n'
        'names = ["Root", "- Child1", "- Child2"]\n'
    )
    s = BookmarkStore(p)
    t = s.tree()
    # /root becomes a submenu (it has children), children are inside it
    assert any(n.kind == "submenu" for n in t), "expected a submenu node after migration"
    # Key invariant: all paths accessible
    assert Path("/root") in s
    assert Path("/child1") in s
    assert Path("/child2") in s


def test_migrate_old_groups(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text(
        '[bookmarks]\n'
        'paths = ["/a"]\n'
        'names = [""]\n'
        '\n'
        '[[bookmarks.groups]]\n'
        'name = "Work"\n'
        'paths = ["/work/proj"]\n'
        'names = ["Proj"]\n'
    )
    s = BookmarkStore(p)
    assert Path("/a") in s
    assert Path("/work/proj") in s


# ── Cycle E: deepcopy isolation (I14) ─────────────────────────────────────────

def test_tree_returns_independent_copy(tmp_path):
    """Mutating the returned tree must not affect store internals."""
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    s.set_tree([BookmarkNode("dir", Path("/x"), "Original")])
    nodes = s.tree()
    nodes[0].name = "MUTATED"
    assert s.tree()[0].name == "Original"


def test_set_tree_stores_independent_copy(tmp_path):
    """Mutating the list passed to set_tree must not affect store internals."""
    p = tmp_path / "bm.toml"
    s = BookmarkStore(p)
    nodes = [BookmarkNode("dir", Path("/y"), "A")]
    s.set_tree(nodes)
    nodes[0].name = "MUTATED"
    assert s.tree()[0].name == "A"
