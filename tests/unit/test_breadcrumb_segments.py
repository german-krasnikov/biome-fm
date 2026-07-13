"""Unit tests for breadcrumb path_segments — no Qt."""
from pathlib import Path

import pytest

from biome_fm.views.breadcrumb_bar import path_segments


def test_posix_path():
    segs = path_segments(Path("/foo/bar"))
    assert segs == [("/", Path("/")), ("foo", Path("/foo")), ("bar", Path("/foo/bar"))]


def test_root_only():
    assert path_segments(Path("/")) == [("/", Path("/"))]


def test_single_child():
    segs = path_segments(Path("/etc"))
    assert len(segs) == 2
    assert segs[1] == ("etc", Path("/etc"))


def test_deep_path():
    segs = path_segments(Path("/a/b/c/d/e"))
    assert len(segs) == 6
    assert segs[-1] == ("e", Path("/a/b/c/d/e"))


def test_home_dir():
    segs = path_segments(Path.home())
    assert segs[-1][1] == Path.home()
    assert segs[0][0] in ("/", "C:\\")  # cross-platform
