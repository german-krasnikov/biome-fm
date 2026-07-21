"""Unit tests for F431 Smart Space Reclaimer — TDD Red phase."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from biome_fm.models.deps_scanner import _DEFAULT_PATTERNS, load_junk_patterns, scan_cleanup_dirs
from biome_fm.presenters.space_reclaimer_presenter import ReclaimEntry, SpaceReclaimerPresenter


# ── load_junk_patterns ────────────────────────────────────────────────────────

def test_load_junk_patterns_no_file():
    assert load_junk_patterns(None) is _DEFAULT_PATTERNS


def test_load_junk_patterns_toml(tmp_path):
    cfg = tmp_path / "junk.toml"
    cfg.write_text('[junk]\npatterns = ["foo", "bar"]\n')
    result = load_junk_patterns(cfg)
    assert result == frozenset({"foo", "bar"})


def test_load_junk_patterns_empty_list(tmp_path):
    cfg = tmp_path / "junk.toml"
    cfg.write_text('[junk]\npatterns = []\n')
    assert load_junk_patterns(cfg) is _DEFAULT_PATTERNS


# ── scan_cleanup_dirs with custom patterns ────────────────────────────────────

def test_scan_custom_patterns(tmp_path):
    (tmp_path / "custom_cache").mkdir()
    found = scan_cleanup_dirs(tmp_path, threading.Event(), patterns=frozenset({"custom_cache"}))
    assert any(p.name == "custom_cache" for p in found)


def test_scan_default_patterns_miss_custom(tmp_path):
    (tmp_path / "custom_cache").mkdir()
    found = scan_cleanup_dirs(tmp_path, threading.Event())
    assert not any(p.name == "custom_cache" for p in found)


# ── SpaceReclaimerPresenter ───────────────────────────────────────────────────

def test_presenter_calls_on_results(tmp_path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "pkg.js").write_text("x")

    results: list[list[ReclaimEntry]] = []
    done = threading.Event()

    def on_results(entries):
        results.append(entries)
        done.set()

    p = SpaceReclaimerPresenter(tmp_path, _DEFAULT_PATTERNS, on_results)
    p.start()
    done.wait(timeout=5)

    assert len(results) == 1
    assert results[0][0].path == nm
    assert results[0][0].size > 0


def test_presenter_cancel(tmp_path):
    (tmp_path / "node_modules").mkdir()

    called = threading.Event()

    def on_results(entries):
        called.set()

    p = SpaceReclaimerPresenter(tmp_path, _DEFAULT_PATTERNS, on_results)
    p.start()
    p.cancel()
    # Give thread time to finish
    time.sleep(0.2)

    assert not called.is_set()
