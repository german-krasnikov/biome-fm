"""Unit tests for copy-resume mtime comparison (>= fix)."""
import os
import threading

from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.models.conflict_resolver import ConflictAction


def _cmd(src_list, dst_dir, strategy=None):
    return ProgressCopyCmd(src_list, dst_dir, None, threading.Event(), lambda *_: None,
                           strategy=strategy)


def test_resume_equal_mtime(tmp_path):
    """>=: partial dst with mtime == src.mtime must not corrupt the copy."""
    src = tmp_path / "src.bin"
    src.write_bytes(b"AABBCC")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    dst = dst_dir / "src.bin"
    dst.write_bytes(b"AA")  # valid prefix
    t = src.stat().st_mtime
    os.utime(dst, (t, t))  # equal timestamp (coarse-FS scenario)
    _cmd([src], dst_dir).execute()
    assert dst.read_bytes() == b"AABBCC"


def test_resume_dst_newer(tmp_path):
    """>=: resume still fires when dst.mtime > src.mtime (no regression)."""
    src = tmp_path / "src.bin"
    src.write_bytes(b"XXYYZZ")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    dst = dst_dir / "src.bin"
    dst.write_bytes(b"XX")  # valid prefix
    os.utime(dst, (src.stat().st_mtime + 10,) * 2)
    _cmd([src], dst_dir).execute()
    assert dst.read_bytes() == b"XXYYZZ"


def test_no_resume_src_newer(tmp_path):
    """>=: src modified after partial — must full-overwrite, not corrupt-append."""
    src = tmp_path / "src.bin"
    src.write_bytes(b"NEWCONTENT")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    dst = dst_dir / "src.bin"
    dst.write_bytes(b"GARBAGE")  # leftover from a different/older source
    os.utime(dst, (src.stat().st_mtime - 10,) * 2)  # dst older → src changed
    _cmd([src], dst_dir).execute()
    assert dst.read_bytes() == b"NEWCONTENT"


def test_force_overwrite_skips_resume(tmp_path):
    """force_overwrite=True (via OVERWRITE strategy) ignores mtime — fresh copy."""
    src = tmp_path / "src.bin"
    src.write_bytes(b"FULL")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    dst = dst_dir / "src.bin"
    dst.write_bytes(b"PA")
    os.utime(dst, (src.stat().st_mtime + 5,) * 2)  # dst newer — would resume without force
    _cmd([src], dst_dir, strategy=ConflictAction.OVERWRITE).execute()
    assert dst.read_bytes() == b"FULL"
