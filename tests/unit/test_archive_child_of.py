"""Unit tests for archive_vfs._child_of helper."""
from biome_fm.models.archive_vfs import _child_of


def test_root_level():
    assert _child_of("file.txt", "") == ("file.txt", False)


def test_nested_returns_top():
    assert _child_of("a/b/c.txt", "") == ("a", True)


def test_prefix_strip():
    assert _child_of("foo/bar.txt", "foo") == ("bar.txt", False)


def test_outside_prefix():
    assert _child_of("other/file.txt", "foo") is None


def test_dotdot_skipped():
    assert _child_of("../escape.txt", "") is None


def test_skip_dot():
    assert _child_of(".", "", skip_dot=True) is None


def test_empty():
    assert _child_of("", "") is None


def test_deeply_nested_prefix():
    assert _child_of("a/b/c/d.txt", "a/b") == ("c", True)
