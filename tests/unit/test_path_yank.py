from pathlib import Path
import pytest
from biome_fm.presenters.path_yank import yank_component

P = Path("/foo/bar.txt")
P_NO_EXT = Path("/foo/bar")


def test_yank_name():
    assert yank_component(P, "n") == "bar.txt"

def test_yank_path():
    assert yank_component(P, "p") == "/foo/bar.txt"

def test_yank_dir():
    assert yank_component(P, "d") == "/foo"

def test_yank_ext():
    assert yank_component(P, "e") == ".txt"

def test_yank_no_ext():
    assert yank_component(P_NO_EXT, "e") == ""

def test_unknown_key_returns_none():
    assert yank_component(P, "x") is None
