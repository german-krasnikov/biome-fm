"""Checksum command — compute file hashes. Not undoable."""
from __future__ import annotations

import hashlib
from pathlib import Path

from biome_fm.commands.base import Command

_CHUNK = 64 * 1024  # 64 KB

try:
    import xxhash as _xxhash
except ImportError:  # pragma: no cover
    _xxhash = None  # type: ignore[assignment]

try:
    import blake3 as _blake3
except ImportError:  # pragma: no cover
    _blake3 = None  # type: ignore[assignment]


def _hash_file(path: Path, algorithm: str) -> str:
    if algorithm == "xxhash":
        h = _xxhash.xxh64() if _xxhash else hashlib.new("md5")
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(_CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    if algorithm == "blake3":
        h = _blake3.blake3() if _blake3 else hashlib.new("sha256")  # type: ignore[attr-defined]
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(_CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    # hashlib covers md5 / sha256 and anything else
    h2 = hashlib.new(algorithm)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h2.update(chunk)
    return h2.hexdigest()


class ChecksumCmd(Command):
    """Compute checksums for file(s). Not undoable."""

    undoable = False

    def __init__(self, paths: list[Path], algorithm: str = "xxhash") -> None:
        self._paths = paths
        self._algorithm = algorithm
        self.result: dict[str, str] = {}

    def execute(self) -> dict[str, str]:  # type: ignore[override]
        self.result = {str(p): _hash_file(p, self._algorithm) for p in self._paths}
        return self.result

    def undo(self) -> None:
        pass
