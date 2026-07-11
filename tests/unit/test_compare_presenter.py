"""Unit tests for ComparePresenter — no Qt."""

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import ComparePresenter, CompareStatus


def _file(name: str, size: int = 100, modified: float = 1000.0) -> FileItem:
    return FileItem(
        name=name, path=Path(f"/left/{name}"), is_dir=False, size=size, modified=modified
    )


def _dir(name: str) -> FileItem:
    return FileItem(name=name, path=Path(f"/left/{name}"), is_dir=True, size=0, modified=0.0)


def _rfile(name: str, size: int = 100, modified: float = 1000.0) -> FileItem:
    return FileItem(
        name=name, path=Path(f"/right/{name}"), is_dir=False, size=size, modified=modified
    )


def _rdir(name: str) -> FileItem:
    return FileItem(name=name, path=Path(f"/right/{name}"), is_dir=True, size=0, modified=0.0)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_empty_both():
    result = ComparePresenter([], []).compare()
    assert result == []


def test_identical_files():
    left = [_file("a.txt"), _file("b.txt")]
    right = [_rfile("a.txt"), _rfile("b.txt")]
    result = ComparePresenter(left, right).compare()
    assert all(e.status == CompareStatus.EQUAL for e in result)
    assert {e.name for e in result} == {"a.txt", "b.txt"}


def test_left_only():
    result = ComparePresenter([_file("a.txt")], []).compare()
    assert len(result) == 1
    assert result[0].status == CompareStatus.LEFT_ONLY
    assert result[0].name == "a.txt"
    assert result[0].right is None


def test_right_only():
    result = ComparePresenter([], [_rfile("b.txt")]).compare()
    assert len(result) == 1
    assert result[0].status == CompareStatus.RIGHT_ONLY
    assert result[0].name == "b.txt"
    assert result[0].left is None


def test_newer_left():
    left = [_file("x.txt", size=50, modified=2000.0)]
    right = [_rfile("x.txt", size=50, modified=1000.0)]
    result = ComparePresenter(left, right).compare()
    assert result[0].status == CompareStatus.NEWER_LEFT


def test_newer_right():
    left = [_file("x.txt", size=50, modified=1000.0)]
    right = [_rfile("x.txt", size=50, modified=2000.0)]
    result = ComparePresenter(left, right).compare()
    assert result[0].status == CompareStatus.NEWER_RIGHT


def test_diff_size():
    left = [_file("x.txt", size=100)]
    right = [_rfile("x.txt", size=200)]
    result = ComparePresenter(left, right).compare()
    assert result[0].status == CompareStatus.DIFF_SIZE


def test_dirs_only_presence():
    left = [_dir("docs"), _dir("shared")]
    right = [_rdir("shared"), _rdir("extra")]
    result = ComparePresenter(left, right).compare()
    by_name = {e.name: e.status for e in result}
    assert by_name["docs"] == CompareStatus.LEFT_ONLY
    assert by_name["shared"] == CompareStatus.EQUAL
    assert by_name["extra"] == CompareStatus.RIGHT_ONLY


def test_mixed_entries_sorted():
    left = [
        _file("eq.txt", size=10, modified=500.0),
        _file("lo.txt"),
        _file("nl.txt", size=10, modified=2000.0),
        _file("ds.txt", size=10),
    ]
    right = [
        _rfile("eq.txt", size=10, modified=500.0),
        _rfile("ro.txt"),
        _rfile("nl.txt", size=10, modified=1000.0),
        _rfile("ds.txt", size=20),
    ]
    result = ComparePresenter(left, right).compare()
    statuses = [e.status for e in result]
    # Expected order: LEFT_ONLY, RIGHT_ONLY, NEWER_LEFT, DIFF_SIZE, EQUAL
    lo_idx = statuses.index(CompareStatus.LEFT_ONLY)
    ro_idx = statuses.index(CompareStatus.RIGHT_ONLY)
    nl_idx = statuses.index(CompareStatus.NEWER_LEFT)
    ds_idx = statuses.index(CompareStatus.DIFF_SIZE)
    eq_idx = statuses.index(CompareStatus.EQUAL)
    assert lo_idx < ro_idx < nl_idx < ds_idx < eq_idx


def test_mtime_tolerance():
    """Difference < 1s → EQUAL, even if size matches."""
    left = [_file("x.txt", size=50, modified=1000.0)]
    right = [_rfile("x.txt", size=50, modified=1000.9)]
    result = ComparePresenter(left, right).compare()
    assert result[0].status == CompareStatus.EQUAL


def test_mtime_tolerance_boundary():
    """Difference exactly 1s → not EQUAL."""
    left = [_file("x.txt", size=50, modified=1000.0)]
    right = [_rfile("x.txt", size=50, modified=1001.0)]
    result = ComparePresenter(left, right).compare()
    assert result[0].status == CompareStatus.NEWER_RIGHT


def test_summary_text():
    left = [_file("lo.txt"), _file("eq.txt", size=5, modified=500.0)]
    right = [
        _rfile("ro.txt"),
        _rfile("eq.txt", size=5, modified=500.0),
        _rfile("nr.txt", size=5, modified=2000.0),
    ]
    # add a matching nr file on left but older
    left.append(_file("nr.txt", size=5, modified=1000.0))
    p = ComparePresenter(left, right)
    p.compare()  # must call compare first to populate cache
    s = p.summary
    assert "1 equal" in s
    assert "1 left only" in s
    assert "1 right only" in s
    assert "1 newer right" in s
