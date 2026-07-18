from pathlib import Path
import pytest
from biome_fm.presenters.predictive_dest import suggest_destination


def _make_dir(tmp_path: Path, name: str, files: list[str]) -> Path:
    d = tmp_path / name
    d.mkdir()
    for f in files:
        (d / f).touch()
    return d


def test_same_ext_suggestion(tmp_path):
    photos = _make_dir(tmp_path, "photos", ["a.jpg", "b.jpg"])
    docs = _make_dir(tmp_path, "docs", ["report.pdf"])
    frecency = [(photos, 5), (docs, 10)]
    assert suggest_destination(Path("new.jpg"), frecency) == photos


def test_no_history_returns_none(tmp_path):
    assert suggest_destination(Path("x.jpg"), []) is None


def test_most_frequent_wins(tmp_path):
    high = _make_dir(tmp_path, "high", ["img.jpg"])
    low = _make_dir(tmp_path, "low", ["img.jpg"])
    frecency = [(high, 10), (low, 2)]
    assert suggest_destination(Path("new.jpg"), frecency) == high


def test_current_dir_excluded(tmp_path):
    cur = _make_dir(tmp_path, "cur", ["pic.jpg"])
    other = _make_dir(tmp_path, "other", ["pic.jpg"])
    frecency = [(cur, 10), (other, 2)]
    assert suggest_destination(Path("new.jpg"), frecency, current_dir=cur) == other
