"""#52 — Verify-After-Copy: SHA-256 checksum verification after file copy."""
import threading

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd


def _cmd(src_dir, dst_dir, cancel, verify):
    return ProgressCopyCmd(
        list(src_dir.iterdir()), dst_dir, None, cancel, lambda *_: None, verify=verify
    )


def test_matching_checksums_pass(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"hello world")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    cancel = threading.Event()
    cmd = _cmd(src_dir, dst_dir, cancel, verify=True)
    cmd.execute()  # must not raise

    assert (dst_dir / "a.txt").read_bytes() == b"hello world"


def test_mismatch_raises(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"original")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    def bad_verify(self, src, dst):
        raise RuntimeError(f"Checksum mismatch: {src.name}")

    monkeypatch.setattr(ProgressCopyCmd, "_verify_file", bad_verify)

    cancel = threading.Event()
    cmd = _cmd(src_dir, dst_dir, cancel, verify=True)
    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        cmd.execute()


def test_verify_false_skips(tmp_path, monkeypatch):
    """With verify=False, no hash is computed — fast path."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_bytes(b"data")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    import hashlib
    calls = []
    real_new = hashlib.sha256

    def counting_sha256(*a, **kw):
        calls.append(1)
        return real_new(*a, **kw)

    monkeypatch.setattr(hashlib, "sha256", counting_sha256)

    cancel = threading.Event()
    cmd = _cmd(src_dir, dst_dir, cancel, verify=False)
    cmd.execute()

    assert len(calls) == 0
