"""Integration tests for file commands using real filesystem + LocalVFS."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.models.vfs import LocalVFS


@pytest.fixture()
def vfs() -> LocalVFS:
    return LocalVFS()


def test_delete_removes_file(tmp_path: Path, vfs: LocalVFS) -> None:
    f = tmp_path / "bye.txt"
    f.write_text("gone")

    DeleteCmd([f], vfs).execute()
    assert not f.exists()


