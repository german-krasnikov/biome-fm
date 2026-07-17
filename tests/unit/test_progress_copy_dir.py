"""#53 — Dir Copy Progress Fix: _copy_dir replaces shutil.copytree with progress."""
import threading

from biome_fm.commands.copy_cmd import ProgressCopyCmd


def test_dir_progress_reported(tmp_path):
    src = tmp_path / "srcdir"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello")
    dst = tmp_path / "dst"
    dst.mkdir()

    reports = []
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: reports.append(a))
    cmd.execute()

    assert (dst / "srcdir" / "a.txt").read_bytes() == b"hello"
    assert len(reports) > 0


def test_nested_dirs(tmp_path):
    src = tmp_path / "root"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "b.txt").write_bytes(b"world")
    dst = tmp_path / "dst"
    dst.mkdir()

    reports = []
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: reports.append(a))
    cmd.execute()

    assert (dst / "root" / "sub" / "b.txt").read_bytes() == b"world"
    assert len(reports) > 0
