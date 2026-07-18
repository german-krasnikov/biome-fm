"""Unit tests for Hotlist — pure Python, no Qt."""
from pathlib import Path
from biome_fm.models.frecency_store import FrecencyEntry
from biome_fm.presenters.hotlist import Hotlist


def _store(*paths: str):
    """Stub store returning FrecencyEntry list in given order."""
    entries = [FrecencyEntry(path=Path(p), visits=1, last_visit=0.0) for p in paths]

    class _Stub:
        def top(self, n: int) -> list[FrecencyEntry]:
            return entries[:n]

    return _Stub()


def test_hotlist_returns_top_paths():
    hl = Hotlist(_store("/a", "/b", "/c"))
    assert hl.items() == [Path("/a"), Path("/b"), Path("/c")]


def test_hotlist_empty_store():
    hl = Hotlist(_store())
    assert hl.items() == []


def test_hotlist_max_items():
    hl = Hotlist(_store(*[f"/{i}" for i in range(10)]))
    assert len(hl.items(limit=5)) == 5


def test_hotlist_deduplicates():
    # FrecencyStore already deduplicates; Hotlist must not re-introduce dupes
    hl = Hotlist(_store("/a", "/a", "/b"))
    result = hl.items()
    assert result.count(Path("/a")) == 1
