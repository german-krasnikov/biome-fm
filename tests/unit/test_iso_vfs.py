"""Unit tests for IsoVFS."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_iso_vfs_requires_pycdlib():
    import biome_fm.models.iso_vfs as mod
    with patch.object(mod, "_HAS_PYCDLIB", False):
        with pytest.raises(ImportError, match="pycdlib"):
            mod.IsoVFS(Path("/fake.iso"))


def _make_vfs(mod, iso_path: Path):
    """Helper: build IsoVFS with pycdlib mocked out."""
    with patch.object(mod, "_HAS_PYCDLIB", True):
        with patch.object(mod, "_pycdlib") as mp:
            fake_iso = type("PyCdlib", (), {"open": lambda *a, **kw: None})()
            mp.PyCdlib.return_value = fake_iso
            return mod.IsoVFS(iso_path)


def test_to_iso_path_root():
    import biome_fm.models.iso_vfs as mod
    iso_path = Path("/some/disk.iso")
    vfs = _make_vfs(mod, iso_path)
    assert vfs._to_iso_path(iso_path) == "/"


def test_to_iso_path_subdir():
    import biome_fm.models.iso_vfs as mod
    iso_path = Path("/some/disk.iso")
    vfs = _make_vfs(mod, iso_path)
    assert vfs._to_iso_path(iso_path / "dir" / "file.txt") == "/dir/file.txt"
