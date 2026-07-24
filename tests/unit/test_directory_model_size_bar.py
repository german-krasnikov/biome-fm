"""Unit tests for DirectoryModel SIZE_BAR_ROLE (Item #45)."""
from pathlib import Path

import pytest

from biome_fm.models.directory_model import COL_SIZE, DirectoryModel
from biome_fm.models.file_item import FileItem


def _dir(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=True, size=0, modified=0.0)


def _file(path: Path, size: int = 100) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=False, size=size, modified=0.0)


def test_size_bar_role_fraction(qapp):
    from biome_fm.models.directory_model import SIZE_BAR_ROLE

    model = DirectoryModel()
    model.set_items([_dir(Path("/a")), _dir(Path("/b"))])
    model.set_dir_size(Path("/a"), 100)
    model.set_dir_size(Path("/b"), 400)

    frac_a = model.data(model.index(0, COL_SIZE), SIZE_BAR_ROLE)
    frac_b = model.data(model.index(1, COL_SIZE), SIZE_BAR_ROLE)

    assert frac_a == pytest.approx(0.25)
    assert frac_b == pytest.approx(1.0)


def test_set_items_recomputes_max_from_cache(qapp):
    from biome_fm.models.directory_model import SIZE_BAR_ROLE

    model = DirectoryModel()
    p = Path("/x")
    model.set_dir_size(p, 500)
    model.set_items([_dir(p)])

    frac = model.data(model.index(0, COL_SIZE), SIZE_BAR_ROLE)
    assert frac == pytest.approx(1.0)


def test_size_bar_role_unknown(qapp):
    from biome_fm.models.directory_model import SIZE_BAR_ROLE

    model = DirectoryModel()
    model.set_items([_dir(Path("/d"))])

    frac = model.data(model.index(0, COL_SIZE), SIZE_BAR_ROLE)
    assert frac == -1.0


def test_size_bar_role_unknown_when_max_nonzero(qapp):
    """Unknown dir must return -1.0 even when another dir has a known size (max > 0)."""
    from biome_fm.models.directory_model import SIZE_BAR_ROLE

    model = DirectoryModel()
    model.set_items([_dir(Path("/a")), _dir(Path("/b"))])
    model.set_dir_size(Path("/a"), 500)  # _max_dir_size is now 500

    frac_b = model.data(model.index(1, COL_SIZE), SIZE_BAR_ROLE)
    assert frac_b == -1.0


def test_size_bar_role_file_returns_negative(qapp):
    from biome_fm.models.directory_model import SIZE_BAR_ROLE

    model = DirectoryModel()
    model.set_items([_file(Path("/f.txt"), 1000)])
    model.set_dir_size(Path("/f.txt"), 1000)  # should not affect bar

    frac = model.data(model.index(0, COL_SIZE), SIZE_BAR_ROLE)
    assert frac == -1.0
