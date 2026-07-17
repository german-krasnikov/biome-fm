"""Unit tests for ComparePresenter.content_compare — content-based dir diff."""
from pathlib import Path

from biome_fm.presenters.compare_presenter import ComparePresenter, CompareStatus


def _make_dirs(tmp_path: Path) -> tuple[Path, Path]:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    return left, right


def test_identical_dirs(tmp_path: Path) -> None:
    left, right = _make_dirs(tmp_path)
    (left / "a.txt").write_bytes(b"same content")
    (right / "a.txt").write_bytes(b"same content")
    p = ComparePresenter([], [])
    result = p.content_compare(left, right)
    assert len(result) == 1
    assert result[0].status == CompareStatus.EQUAL


def test_different_content(tmp_path: Path) -> None:
    left, right = _make_dirs(tmp_path)
    (left / "a.txt").write_bytes(b"hello")
    (right / "a.txt").write_bytes(b"world")
    p = ComparePresenter([], [])
    result = p.content_compare(left, right)
    assert len(result) == 1
    assert result[0].status == CompareStatus.DIFF_SIZE


def test_large_file_fallback(tmp_path: Path) -> None:
    """Files >10 MB fall back to size+mtime comparison."""
    left, right = _make_dirs(tmp_path)
    _11MB = 11 * 1024 * 1024
    lf = left / "big.bin"
    rf = right / "big.bin"
    lf.write_bytes(b"x" * _11MB)
    rf.write_bytes(b"x" * _11MB)
    p = ComparePresenter([], [])
    result = p.content_compare(left, right)
    # same size + mtime within tolerance → EQUAL
    assert len(result) == 1
    assert result[0].status == CompareStatus.EQUAL
