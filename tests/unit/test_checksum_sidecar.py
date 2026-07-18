"""F339 — Checksum sidecar verification tests."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def _write_sidecar(path: Path, alg: str, content: bytes) -> Path:
    h = hashlib.new(alg, content).hexdigest()
    ext_map = {"md5": ".md5", "sha256": ".sha256", "sha1": ".sha1", "sha512": ".sha512"}
    sidecar = path.with_suffix(path.suffix + ext_map[alg])
    sidecar.write_text(h + "\n")
    return sidecar


class TestFindSidecar:
    def test_find_sidecar_all_algorithms(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import find_sidecar

        data = b"hello"
        f = tmp_path / "file.bin"
        f.write_bytes(data)

        for alg in ("md5", "sha256", "sha1", "sha512"):
            sidecar = _write_sidecar(f, alg, data)
            result = find_sidecar(f)
            assert result is not None
            assert result[0] == sidecar
            assert result[1] == alg
            sidecar.unlink()

    def test_find_sidecar_returns_none_when_missing(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import find_sidecar

        f = tmp_path / "file.bin"
        f.write_bytes(b"data")
        assert find_sidecar(f) is None


class TestVerifySidecar:
    def test_verify_sidecar_match(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import verify_sidecar

        data = b"hello world"
        f = tmp_path / "archive.tar.gz"
        f.write_bytes(data)
        _write_sidecar(f, "sha256", data)

        ok, msg = verify_sidecar(f)
        assert ok
        assert "sha256" in msg

    def test_verify_sidecar_mismatch(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import verify_sidecar

        data = b"original"
        f = tmp_path / "file.bin"
        f.write_bytes(data)
        # write sidecar for different content
        sidecar = f.with_suffix(f.suffix + ".md5")
        sidecar.write_text("deadbeefdeadbeef\n")

        ok, msg = verify_sidecar(f)
        assert not ok

    def test_no_sidecar_raises(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import verify_sidecar

        f = tmp_path / "lonely.bin"
        f.write_bytes(b"data")

        with pytest.raises(FileNotFoundError):
            verify_sidecar(f)
