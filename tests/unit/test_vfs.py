"""Tests for LocalVFS — no Qt dependency."""

from pathlib import Path

from biome_fm.models.vfs import LocalVFS


class TestLocalVFS:
    def test_listdir_returns_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")

        vfs = LocalVFS()
        items = vfs.listdir(tmp_path)

        assert len(items) == 2
        names = {i.name for i in items}
        assert names == {"a.txt", "b.txt"}

    def test_listdir_distinguishes_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").touch()
        (tmp_path / "subdir").mkdir()

        vfs = LocalVFS()
        items = vfs.listdir(tmp_path)

        dirs = [i for i in items if i.is_dir]
        files = [i for i in items if not i.is_dir]
        assert len(dirs) == 1
        assert len(files) == 1
        assert dirs[0].name == "subdir"

    def test_copy_file(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("data")
        dst = tmp_path / "dst.txt"

        vfs = LocalVFS()
        vfs.copy(src, dst)

        assert dst.read_text() == "data"
        assert src.exists()

    def test_move_file(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("data")
        dst = tmp_path / "dst.txt"

        vfs = LocalVFS()
        vfs.move(src, dst)

        assert dst.read_text() == "data"
        assert not src.exists()

    def test_delete_file(self, tmp_path: Path) -> None:
        f = tmp_path / "to_delete.txt"
        f.write_text("bye")

        vfs = LocalVFS()
        vfs.delete(f)

        assert not f.exists()

    def test_mkdir(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "new" / "nested"

        vfs = LocalVFS()
        vfs.mkdir(new_dir)

        assert new_dir.is_dir()

    def test_exists(self, tmp_path: Path) -> None:
        f = tmp_path / "exists.txt"
        vfs = LocalVFS()

        assert not vfs.exists(f)
        f.touch()
        assert vfs.exists(f)
