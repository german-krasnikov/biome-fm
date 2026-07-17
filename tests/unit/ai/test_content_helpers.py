"""Unit tests for ai/types content helpers."""
from pathlib import Path

from biome_fm.ai.types import FileContent, _file_text


def test_file_text_format():
    fc = FileContent(path=Path("/some/file.py"), content="print('hi')")
    assert _file_text(fc) == "[file.py]\nprint('hi')"


def test_file_text_multiline():
    fc = FileContent(path=Path("/a/b.md"), content="line1\nline2")
    assert _file_text(fc) == "[b.md]\nline1\nline2"
