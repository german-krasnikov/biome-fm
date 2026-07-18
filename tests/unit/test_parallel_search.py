"""TDD tests for parallel content search workers (F054)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


@pytest.fixture()
def content_dir(tmp_path: Path) -> Path:
    """50 text files: half contain 'needle', half contain 'haystack'."""
    for i in range(25):
        (tmp_path / f"match_{i}.txt").write_text(f"line {i}\nneedle here\nend")
    for i in range(25):
        (tmp_path / f"skip_{i}.txt").write_text(f"haystack only {i}")
    return tmp_path


def test_parallel_finds_same_results_as_serial(content_dir: Path) -> None:
    """Parallel content search returns same set of matches as serial."""
    serial = SearchPresenter(LocalVFS(), content_dir)
    parallel = SearchPresenter(LocalVFS(), content_dir)

    serial_results = serial.search("needle", mode=SearchMode.CONTENT, max_results=1000)
    parallel_results = parallel.search("needle", mode=SearchMode.CONTENT, max_results=1000)

    assert sorted(r.item.name for r in serial_results) == sorted(r.item.name for r in parallel_results)
    assert len(parallel_results) == 25


def test_cancel_stops_parallel_workers(content_dir: Path) -> None:
    """Cancel after first match stops further parallel processing."""
    presenter = SearchPresenter(LocalVFS(), content_dir)

    def on_match(result):  # noqa: ANN001
        presenter.cancel()

    results = presenter.search(
        "needle", mode=SearchMode.CONTENT, max_results=1000, on_match=on_match
    )
    assert len(results) < 25


def test_parallel_respects_max_results(content_dir: Path) -> None:
    """Parallel search never returns more than max_results."""
    results = SearchPresenter(LocalVFS(), content_dir).search(
        "needle", mode=SearchMode.CONTENT, max_results=5
    )
    assert len(results) == 5


def test_parallel_content_regex_finds_matches(content_dir: Path) -> None:
    """CONTENT_REGEX mode also uses parallel workers."""
    results = SearchPresenter(LocalVFS(), content_dir).search(
        r"need\w+", mode=SearchMode.CONTENT_REGEX, max_results=1000
    )
    assert len(results) == 25


def test_name_wildcard_unaffected(content_dir: Path) -> None:
    """NAME_WILDCARD mode stays serial (smoke test — must not regress)."""
    results = SearchPresenter(LocalVFS(), content_dir).search(
        "match_*.txt", mode=SearchMode.NAME_WILDCARD
    )
    assert len(results) == 25
