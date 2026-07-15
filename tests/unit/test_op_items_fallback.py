"""Test the effective items fallback logic (marked → cursor → empty)."""
from pathlib import Path
from biome_fm.models.file_item import FileItem


def _item(name, is_dir=False):
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


def _op_items_logic(marked, cursor):
    """Extracted pure logic of _op_items — testable without Qt."""
    if marked:
        return marked
    return [cursor] if cursor and cursor.name != ".." else []


def test_marked_items_take_priority():
    marked = [_item("a.txt"), _item("b.txt")]
    cursor = _item("c.txt")
    assert _op_items_logic(marked, cursor) == marked


def test_cursor_fallback_when_no_marks():
    cursor = _item("file.txt")
    assert _op_items_logic([], cursor) == [cursor]


def test_dotdot_excluded():
    dotdot = _item("..", is_dir=True)
    assert _op_items_logic([], dotdot) == []


def test_none_cursor():
    assert _op_items_logic([], None) == []
