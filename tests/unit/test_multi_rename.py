"""TDD: MultiRenameCmd + RenamePresenter."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

from biome_fm.commands.multi_rename_cmd import MultiRenameCmd
from biome_fm.models.file_item import FileItem
from biome_fm.presenters.rename_presenter import RenamePresenter


def item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=is_dir, size=0, modified=0.0)


def vfs() -> MagicMock:
    m = MagicMock()
    m.move = MagicMock()
    return m


# ── MultiRenameCmd ──────────────────────────────────────────────────────────

def test_multi_rename_cmd_execute():
    v = vfs()
    renames = [
        (Path("/tmp/a.txt"), Path("/tmp/b.txt")),
        (Path("/tmp/c.txt"), Path("/tmp/d.txt")),
        (Path("/tmp/e.txt"), Path("/tmp/f.txt")),
    ]
    MultiRenameCmd(renames, v).execute()
    v.move.assert_has_calls([
        call(Path("/tmp/a.txt"), Path("/tmp/b.txt")),
        call(Path("/tmp/c.txt"), Path("/tmp/d.txt")),
        call(Path("/tmp/e.txt"), Path("/tmp/f.txt")),
    ])


def test_multi_rename_cmd_undo():
    v = vfs()
    renames = [
        (Path("/tmp/a.txt"), Path("/tmp/b.txt")),
        (Path("/tmp/c.txt"), Path("/tmp/d.txt")),
    ]
    cmd = MultiRenameCmd(renames, v)
    cmd.execute()
    v.move.reset_mock()
    cmd.undo()
    # reversed order
    v.move.assert_has_calls([
        call(Path("/tmp/d.txt"), Path("/tmp/c.txt")),
        call(Path("/tmp/b.txt"), Path("/tmp/a.txt")),
    ])


def test_multi_rename_cmd_empty_list():
    v = vfs()
    cmd = MultiRenameCmd([], v)
    cmd.execute()
    cmd.undo()
    v.move.assert_not_called()


def test_multi_rename_cmd_is_undoable():
    assert MultiRenameCmd([], vfs()).undoable is True


# ── RenamePresenter: regex ──────────────────────────────────────────────────

def test_regex_simple():
    p = RenamePresenter([item("foo_file.txt"), item("foo_doc.pdf")])
    result = [pv.new_name for pv in p.apply_regex("foo", "bar")]
    assert result == ["bar_file.txt", "bar_doc.pdf"]


def test_regex_groups():
    # no extension — (.+) captures only the stem, result is unambiguous
    p = RenamePresenter([item("2024_photo"), item("2023_photo")])
    result = [pv.new_name for pv in p.apply_regex(r"(\d{4})_(.+)", r"\2_\1")]
    assert result == ["photo_2024", "photo_2023"]


def test_regex_invalid_pattern():
    p = RenamePresenter([item("file.txt")])
    previews = p.apply_regex("[invalid", "bar")
    assert previews[0].new_name == "file.txt"


# ── RenamePresenter: counter ────────────────────────────────────────────────

def test_counter_basic():
    p = RenamePresenter([item("a.txt"), item("b.txt"), item("c.txt")])
    result = [pv.new_name for pv in p.apply_counter("photo_{n:03d}")]
    assert result == ["photo_001.txt", "photo_002.txt", "photo_003.txt"]


def test_counter_custom_start_step():
    p = RenamePresenter([item("x.jpg"), item("y.jpg")])
    result = [pv.new_name for pv in p.apply_counter("img_{n}", start=10, step=5)]
    assert result == ["img_10.jpg", "img_15.jpg"]


# ── RenamePresenter: extension ──────────────────────────────────────────────

def test_extension_change():
    p = RenamePresenter([item("doc.txt"), item("note.txt")])
    result = [pv.new_name for pv in p.apply_extension("md")]
    assert result == ["doc.md", "note.md"]


def test_extension_dirs_excluded():
    p = RenamePresenter([item("folder", is_dir=True), item("file.txt")])
    previews = p.apply_extension("md")
    assert previews[0].new_name == "folder"
    assert previews[1].new_name == "file.md"


# ── Conflict detection ──────────────────────────────────────────────────────

def test_conflict_detection():
    # a.txt → x.txt, b.txt → x.txt → both conflict
    p = RenamePresenter([item("a.txt"), item("b.txt")])
    previews = p.apply_regex(r"[ab]", "x")
    assert all(pv.conflict for pv in previews)
    assert p.has_conflicts


def test_get_renames_filters_conflicts():
    # a→x.txt conflict, b→x.txt conflict, c unchanged → empty
    p = RenamePresenter([item("a.txt"), item("b.txt"), item("c.txt")])
    previews = p.apply_regex(r"[ab]", "x")
    assert p.get_renames(previews) == []


def test_get_renames_filters_unchanged():
    p = RenamePresenter([item("foo.txt"), item("bar.txt")])
    previews = p.apply_regex("foo", "baz")
    renames = p.get_renames(previews)
    assert len(renames) == 1
    assert renames[0] == (Path("/tmp/foo.txt"), Path("/tmp/baz.txt"))
