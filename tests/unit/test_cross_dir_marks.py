from pathlib import Path

import pytest

from biome_fm.presenters.cross_marks import CrossDirMarks


@pytest.fixture
def marks() -> CrossDirMarks:
    return CrossDirMarks()


A = Path("/a")
B = Path("/b")
F1 = A / "file1.txt"
F2 = B / "file2.txt"
F3 = B / "file3.txt"


def test_add_global_mark(marks: CrossDirMarks) -> None:
    marks.add(A, F1)
    assert F1 in marks.all_paths()


def test_marks_across_dirs(marks: CrossDirMarks) -> None:
    marks.add(A, F1)
    marks.add(B, F2)
    paths = marks.all_paths()
    assert F1 in paths and F2 in paths


def test_clear_global_marks(marks: CrossDirMarks) -> None:
    marks.add(A, F1)
    marks.add(B, F2)
    marks.clear()
    assert marks.all_paths() == []


def test_global_mark_count(marks: CrossDirMarks) -> None:
    marks.add(A, F1)
    marks.add(B, F2)
    marks.add(B, F3)
    assert marks.count() == 3


def test_remove_single_mark(marks: CrossDirMarks) -> None:
    marks.add(A, F1)
    marks.add(B, F2)
    marks.remove(A, F1)
    assert F1 not in marks.all_paths()
    assert F2 in marks.all_paths()
