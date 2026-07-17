"""TDD unit tests for ChecksumCmd — Red phase."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def _write(tmp_path: Path, name: str, data: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


class TestChecksumCmd:
    def test_md5_checksum(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        data = b"hello biome"
        f = _write(tmp_path, "a.txt", data)
        result = ChecksumCmd([f], algorithm="md5").execute()
        assert result[str(f)] == hashlib.md5(data).hexdigest()

    def test_sha256_checksum(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        data = b"hello biome"
        f = _write(tmp_path, "a.txt", data)
        result = ChecksumCmd([f], algorithm="sha256").execute()
        assert result[str(f)] == hashlib.sha256(data).hexdigest()

    def test_xxhash_checksum(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        data = b"hello biome"
        f = _write(tmp_path, "a.txt", data)
        result = ChecksumCmd([f], algorithm="xxhash").execute()
        assert len(result[str(f)]) > 0

    def test_blake3_checksum(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        data = b"hello biome"
        f = _write(tmp_path, "a.txt", data)
        result = ChecksumCmd([f], algorithm="blake3").execute()
        assert len(result[str(f)]) > 0

    def test_chunked_read(self, tmp_path: Path) -> None:
        """File > 64 KB should still produce correct MD5."""
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        data = b"x" * (128 * 1024)  # 128 KB
        f = _write(tmp_path, "big.bin", data)
        result = ChecksumCmd([f], algorithm="md5").execute()
        assert result[str(f)] == hashlib.md5(data).hexdigest()

    def test_multiple_files(self, tmp_path: Path) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        a = _write(tmp_path, "a.txt", b"aaa")
        b = _write(tmp_path, "b.txt", b"bbb")
        result = ChecksumCmd([a, b], algorithm="md5").execute()
        assert result[str(a)] == hashlib.md5(b"aaa").hexdigest()
        assert result[str(b)] == hashlib.md5(b"bbb").hexdigest()
