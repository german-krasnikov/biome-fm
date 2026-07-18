"""F243 — Additional Sort/Time Columns: atime/ctime/owner."""
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.directory_model import COL_ATIME, COL_OWNER, HEADERS


def test_file_item_has_atime_ctime_owner():
    item = FileItem(
        name="a.txt", path=Path("/a.txt"), is_dir=False, size=10, modified=1.0,
        atime=2.0, ctime=3.0, owner="alice",
    )
    assert item.atime == 2.0
    assert item.ctime == 3.0
    assert item.owner == "alice"


def test_file_item_defaults():
    item = FileItem(name="a.txt", path=Path("/a.txt"), is_dir=False, size=10, modified=1.0)
    assert item.atime == 0.0
    assert item.ctime == 0.0
    assert item.owner == ""


def test_directory_model_has_extra_columns():
    assert COL_ATIME == 4
    assert COL_OWNER == 5
    assert len(HEADERS) >= 6
    assert "Accessed" in HEADERS
    assert "Owner" in HEADERS
