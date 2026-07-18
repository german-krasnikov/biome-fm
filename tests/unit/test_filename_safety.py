"""Unit tests for cross-filesystem filename safety check."""
import pytest
from biome_fm.commands.copy_cmd import _check_filename_safety


def test_legal_filename_passes():
    assert _check_filename_safety("normal_file.txt") is None


def test_illegal_chars_detected():
    result = _check_filename_safety("file:name.txt")
    assert result is not None
    assert ":" not in result


def test_sanitize_suggestion():
    result = _check_filename_safety("what?<is>this.txt")
    assert result == "what__is_this.txt"


def test_multiple_illegal_chars():
    # All FAT/NTFS illegal chars replaced
    result = _check_filename_safety('a\\b/c:d*e?f"g<h>i|j.txt')
    assert result is not None
    assert not any(c in result for c in r'\/:*?"<>|')


def test_control_chars_replaced():
    result = _check_filename_safety("file\x00name.txt")
    assert result is not None
    assert "\x00" not in result


def test_reserved_name_windows():
    assert _check_filename_safety("CON") == "_CON"


def test_reserved_name_with_extension():
    assert _check_filename_safety("NUL.txt") == "_NUL.txt"


def test_reserved_name_trailing_dot():
    assert _check_filename_safety("CON.") == "_CON."


def test_reserved_name_com():
    assert _check_filename_safety("COM1") == "_COM1"


def test_reserved_name_case_insensitive():
    assert _check_filename_safety("con") == "_con"


def test_non_reserved_name_passes():
    assert _check_filename_safety("console.txt") is None


def test_lpt_reserved():
    assert _check_filename_safety("LPT9") is not None


def test_combined_reserved_and_illegal():
    result = _check_filename_safety("CON:stream")
    assert result is not None
    assert ":" not in result
    assert result == "CON_stream"


def test_clean_name_no_extension():
    assert _check_filename_safety("myfile") is None


def test_copy_dir_checks_children(tmp_path):
    import threading
    from biome_fm.commands.copy_cmd import ProgressCopyCmd
    from biome_fm.models.vfs import LocalVFS

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "good.txt").write_text("ok")
    (src_dir / "bad:file.txt").write_text("bad")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    cmd = ProgressCopyCmd(
        sources=[src_dir],
        dest_dir=dst_dir,
        vfs=LocalVFS(),
        cancel=threading.Event(),
        report=lambda *_: None,
    )
    with pytest.raises(ValueError, match="Illegal filename"):
        cmd.execute()
