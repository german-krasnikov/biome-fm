"""Unit tests for DmgVFS."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import biome_fm.models.dmg_vfs as mod


def test_dmg_vfs_requires_macos():
    with patch.object(mod.sys, "platform", "linux"):
        with pytest.raises(RuntimeError, match="macOS"):
            mod.DmgVFS(Path("/fake.dmg"))


def test_real_path_not_mounted():
    with patch.object(mod.sys, "platform", "darwin"):
        vfs = mod.DmgVFS(Path("/fake.dmg"))
    with pytest.raises(RuntimeError, match="Not mounted"):
        vfs._real(Path("/fake.dmg"))


def test_real_path_mapping():
    dmg = Path("/fake.dmg")
    with patch.object(mod.sys, "platform", "darwin"):
        vfs = mod.DmgVFS(dmg)
    vfs._mount = Path("/Volumes/test")
    assert vfs._real(dmg / "dir") == Path("/Volumes/test/dir")


def test_unmount_calls_hdiutil():
    dmg = Path("/fake.dmg")
    with patch.object(mod.sys, "platform", "darwin"):
        vfs = mod.DmgVFS(dmg)
    vfs._mount = Path("/Volumes/test")

    with patch.object(mod.subprocess, "run") as mock_run:
        vfs.unmount()
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[:2] == ["hdiutil", "detach"]
        assert "/Volumes/test" in args
