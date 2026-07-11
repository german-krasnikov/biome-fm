"""Tests for SearchPresenter — TDD, no Qt."""

from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """
    root/
      file1.txt  ("hello world")
      file2.py   ("def foo(): pass")
      sub/
        file3.txt  ("hello again")
        deep/
          file4.log  ("error: something")
    """
    (tmp_path / "file1.txt").write_text("hello world\n")
    (tmp_path / "file2.py").write_text("def foo(): pass\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "file3.txt").write_text("hello again\n")
    deep = sub / "deep"
    deep.mkdir()
    (deep / "file4.log").write_text("error: something\n")
    return tmp_path


def _make_item(path: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=is_dir, size=0, modified=0.0)


# ---------------------------------------------------------------------------
# NAME_WILDCARD
# ---------------------------------------------------------------------------


def test_search_by_name_wildcard(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*.txt")
    names = {r.item.name for r in results}
    assert names == {"file1.txt", "file3.txt"}


def test_search_no_matches(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*.xyz")
    assert results == []


def test_search_dirs_included_in_name_search(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("sub")
    names = {r.item.name for r in results}
    assert "sub" in names


# ---------------------------------------------------------------------------
# NAME_REGEX
# ---------------------------------------------------------------------------


def test_search_by_name_regex(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(r"file\d+", mode=SearchMode.NAME_REGEX)
    names = {r.item.name for r in results}
    assert names == {"file1.txt", "file2.py", "file3.txt", "file4.log"}


def test_search_regex_no_match(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(r"zzz\d+", mode=SearchMode.NAME_REGEX)
    assert results == []


# ---------------------------------------------------------------------------
# Recursive
# ---------------------------------------------------------------------------


def test_search_recursive(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*.log")
    names = {r.item.name for r in results}
    assert "file4.log" in names


def test_search_finds_in_deep_subdir(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("file4.log")
    assert len(results) == 1
    assert results[0].item.path == tree / "sub" / "deep" / "file4.log"


# ---------------------------------------------------------------------------
# CONTENT
# ---------------------------------------------------------------------------


def test_search_by_content(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("hello", mode=SearchMode.CONTENT)
    names = {r.item.name for r in results}
    assert names == {"file1.txt", "file3.txt"}


def test_search_content_context(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("hello world", mode=SearchMode.CONTENT)
    assert len(results) == 1
    assert results[0].context == "hello world"


def test_search_content_context_max_200_chars(tree: Path, tmp_path: Path) -> None:
    long_line = "needle" + "x" * 300
    (tmp_path / "big.txt").write_text(long_line)
    results = SearchPresenter(LocalVFS(), tmp_path).search("needle", mode=SearchMode.CONTENT)
    assert len(results) == 1
    assert len(results[0].context) <= 200


def test_search_binary_skip(tree: Path, tmp_path: Path) -> None:
    # Write binary content that is not valid UTF-8
    (tmp_path / "binary.bin").write_bytes(b"\x80\x81\x82\x00\xff\xfe")
    # Should not raise; binary file is silently skipped
    results = SearchPresenter(LocalVFS(), tmp_path).search("hello", mode=SearchMode.CONTENT)
    names = {r.item.name for r in results}
    assert "binary.bin" not in names


# ---------------------------------------------------------------------------
# max_results
# ---------------------------------------------------------------------------


def test_search_max_results(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*", max_results=2)
    assert len(results) <= 2


def test_search_max_results_zero(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*", max_results=0)
    assert results == []


# ---------------------------------------------------------------------------
# Empty query
# ---------------------------------------------------------------------------


def test_search_empty_query_wildcard(tree: Path) -> None:
    assert SearchPresenter(LocalVFS(), tree).search("") == []


def test_search_empty_query_regex(tree: Path) -> None:
    assert SearchPresenter(LocalVFS(), tree).search("", mode=SearchMode.NAME_REGEX) == []


def test_search_empty_query_content(tree: Path) -> None:
    assert SearchPresenter(LocalVFS(), tree).search("", mode=SearchMode.CONTENT) == []


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


def test_is_cancelled_initial_false(tree: Path) -> None:
    p = SearchPresenter(LocalVFS(), tree)
    assert not p.is_cancelled


def test_cancel_sets_flag(tree: Path) -> None:
    p = SearchPresenter(LocalVFS(), tree)
    p.cancel()
    assert p.is_cancelled


def test_search_cancel() -> None:
    """Cancel called during listdir halts further processing."""

    class CancelOnFirstListVFS:
        """Calls presenter.cancel() on first listdir, then returns 500 items."""

        def __init__(self) -> None:
            self.presenter: SearchPresenter | None = None
            self._called = False

        def listdir(self, path: Path) -> list[FileItem]:
            if not self._called and self.presenter is not None:
                self._called = True
                self.presenter.cancel()
            return [
                _make_item(path / f"file{i}.txt")
                for i in range(500)
            ]

    fake_vfs = CancelOnFirstListVFS()
    presenter = SearchPresenter(fake_vfs, Path("/fake"))  # type: ignore[arg-type]
    fake_vfs.presenter = presenter

    results = presenter.search("*.txt", max_results=10_000)
    # Cancel was set before items were processed → 0 results
    assert len(results) == 0
    assert presenter.is_cancelled


# ---------------------------------------------------------------------------
# Permission / OSError
# ---------------------------------------------------------------------------


def test_search_permission_error(tree: Path, tmp_path: Path) -> None:
    """OSError from listdir on a subdir is swallowed; rest of tree is searched."""

    class PermErrorVFS:
        """Raises OSError for paths named 'forbidden', uses LocalVFS otherwise."""

        _local = LocalVFS()

        def listdir(self, path: Path) -> list[FileItem]:
            if path.name == "forbidden":
                raise OSError("Permission denied")
            return self._local.listdir(path)

    forbidden = tmp_path / "forbidden"
    forbidden.mkdir()
    (forbidden / "secret.txt").write_text("hidden")
    (tmp_path / "visible.txt").write_text("found")

    results = SearchPresenter(PermErrorVFS(), tmp_path).search("*.txt")  # type: ignore[arg-type]
    names = {r.item.name for r in results}
    assert "visible.txt" in names
    assert "secret.txt" not in names
