"""Tests for ExportListingCmd."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str, size: int = 100, mtime: float = 1_700_000_000.0) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=size, modified=mtime)


def test_txt_format(tmp_path: Path) -> None:
    from biome_fm.commands.export_listing_cmd import ExportListingCmd

    items = [_item("a.txt", 42), _item("b.py", 1024)]
    dest = tmp_path / "listing.txt"
    ExportListingCmd(items, dest, fmt="txt").execute()

    lines = dest.read_text().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("a.txt\t")
    assert "42" in lines[0]
    assert lines[1].startswith("b.py\t")


def test_csv_format(tmp_path: Path) -> None:
    from biome_fm.commands.export_listing_cmd import ExportListingCmd

    items = [_item("x.txt", 10)]
    dest = tmp_path / "listing.csv"
    ExportListingCmd(items, dest, fmt="csv").execute()

    rows = list(csv.reader(dest.read_text().splitlines()))
    assert rows[0] == ["name", "size", "modified"]
    assert rows[1][0] == "x.txt"
    assert rows[1][1] == "10"


def test_empty_dir(tmp_path: Path) -> None:
    from biome_fm.commands.export_listing_cmd import ExportListingCmd

    dest = tmp_path / "empty.txt"
    ExportListingCmd([], dest, fmt="txt").execute()
    assert dest.read_text() == ""


def test_not_undoable() -> None:
    from biome_fm.commands.export_listing_cmd import ExportListingCmd

    assert ExportListingCmd([], Path("/tmp/x.txt")).undoable is False
