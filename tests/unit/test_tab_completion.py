"""F270 — Command Line Tab-Completion (path_completions utility)."""
from pathlib import Path

from biome_fm.utils.path_completion import path_completions


def test_path_completion_returns_matches(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").touch()
    (tmp_path / "hello_world.txt").touch()
    (tmp_path / "other.py").touch()

    matches = path_completions(str(tmp_path / "hello"))
    assert len(matches) == 2
    assert all("hello" in m for m in matches)


def test_non_path_skips_completion() -> None:
    assert path_completions("ls") == []
    assert path_completions("") == []
    assert path_completions("grep foo") == []


def test_absolute_path_recognized(tmp_path: Path) -> None:
    (tmp_path / "abc.txt").touch()
    matches = path_completions(str(tmp_path / "abc"))
    assert len(matches) == 1


def test_tilde_path_recognized() -> None:
    # ~/. should complete to something (home dir entries)
    matches = path_completions("~/")
    # just assert it doesn't raise and returns a list
    assert isinstance(matches, list)
