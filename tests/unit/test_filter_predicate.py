"""Tests for advanced filter predicate parsing (F415)."""
import time
import pytest
from biome_fm.models.filter_predicate import parse_filter, filter_accepts, FilterSpec


def test_parse_size_gt():
    spec = parse_filter("size:>10m")
    assert spec.size_op == ">"
    assert spec.size_bytes == 10 * 1024 * 1024


def test_parse_size_lt():
    spec = parse_filter("size:<1k")
    assert spec.size_op == "<"
    assert spec.size_bytes == 1024


def test_parse_mod_today():
    spec = parse_filter("mod:today")
    assert spec.mod_period == "today"


def test_parse_ext_and_name():
    spec = parse_filter("ext:py foo")
    assert spec.ext == "py"
    assert spec.name == "foo"


def test_parse_combined():
    spec = parse_filter("size:>1m ext:py mod:today bar")
    assert spec.size_op == ">"
    assert spec.size_bytes == 1024 * 1024
    assert spec.ext == "py"
    assert spec.mod_period == "today"
    assert spec.name == "bar"


def test_filter_accepts_size_gt():
    spec = parse_filter("size:>1m")
    assert filter_accepts(spec, "big.bin", 2 * 1024 * 1024, time.time(), False)
    assert not filter_accepts(spec, "tiny.bin", 500, time.time(), False)


def test_filter_accepts_mod_today():
    spec = parse_filter("mod:today")
    recent = time.time() - 100
    old = time.time() - 2 * 86400
    assert filter_accepts(spec, "new.txt", 0, recent, False)
    assert not filter_accepts(spec, "old.txt", 0, old, False)


def test_filter_accepts_ext():
    spec = parse_filter("ext:py")
    assert filter_accepts(spec, "script.py", 0, time.time(), False)
    assert not filter_accepts(spec, "notes.txt", 0, time.time(), False)


def test_filter_accepts_name():
    spec = parse_filter("read")
    assert filter_accepts(spec, "readme.txt", 0, time.time(), False)
    assert not filter_accepts(spec, "config.py", 0, time.time(), False)


def test_filter_accepts_dir_skips_size():
    spec = parse_filter("size:>1m")
    # directories skip size check — always pass
    assert filter_accepts(spec, "mydir", 0, time.time(), True)
