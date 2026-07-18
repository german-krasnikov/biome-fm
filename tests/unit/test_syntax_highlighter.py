"""Unit tests for PygmentsHighlighter (F260) — no Qt needed."""
from pygments.token import Token

from biome_fm.views.editor_highlighter import _build_formats


def test_build_formats_has_keyword() -> None:
    formats = _build_formats()
    assert Token.Keyword in formats


def test_build_formats_has_comment() -> None:
    formats = _build_formats()
    assert Token.Comment in formats


def test_large_file_threshold() -> None:
    from biome_fm.views.editor_highlighter import _MAX_FILE_BYTES
    assert _MAX_FILE_BYTES == 512 * 1024
