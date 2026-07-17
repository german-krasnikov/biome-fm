"""Unit tests for ClipboardService — Qt-free clipboard."""
from pathlib import Path

import pytest

from biome_fm.models.clipboard_service import ClipboardService


def test_copy_sets_paths():
    svc = ClipboardService()
    paths = [Path("/a/b"), Path("/c/d")]
    svc.copy(paths)
    result, is_cut = svc.paste(Path("/dest"))
    assert set(result) == set(paths)
    assert not is_cut


def test_cut_sets_paths():
    svc = ClipboardService()
    paths = [Path("/a/b")]
    svc.cut(paths)
    result, is_cut = svc.paste(Path("/dest"))
    assert result == paths
    assert is_cut


def test_paste_returns_paths_and_flag():
    svc = ClipboardService()
    svc.copy([Path("/x")])
    paths, flag = svc.paste(Path("/y"))
    assert paths == [Path("/x")]
    assert flag is False


def test_paste_cut_clears():
    svc = ClipboardService()
    svc.cut([Path("/x")])
    svc.paste(Path("/y"))
    result, flag = svc.paste(Path("/y"))
    assert result == []
    assert not flag


def test_paste_empty_no_op():
    svc = ClipboardService()
    result, flag = svc.paste(Path("/dest"))
    assert result == []
    assert not flag


def test_has_cut_empty_after_copy():
    svc = ClipboardService()
    svc.copy([Path("/x")])
    assert svc.has_cut == set()


def test_has_cut_returns_paths_after_cut():
    svc = ClipboardService()
    paths = [Path("/x"), Path("/y")]
    svc.cut(paths)
    assert svc.has_cut == set(paths)


def test_clear_resets_state():
    svc = ClipboardService()
    svc.cut([Path("/x")])
    svc.clear()
    assert svc.has_cut == set()
    result, _ = svc.paste(Path("/y"))
    assert result == []
