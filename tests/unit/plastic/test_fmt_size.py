"""Unit tests for _fmt_size() — pure Python, no Qt."""
from __future__ import annotations

from biome_fm.plastic._models import _fmt_size


def test_fmt_size_bytes():
    assert _fmt_size(512) == "512 B"


def test_fmt_size_kb():
    assert _fmt_size(1500) == "1 KB"


def test_fmt_size_mb():
    assert _fmt_size(2_500_000) == "2 MB"


def test_fmt_size_gb():
    assert _fmt_size(5_000_000_000) == "5 GB"


def test_fmt_size_tb():
    assert _fmt_size(1024 ** 4) == "1.0 TB"
