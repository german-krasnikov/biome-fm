"""Tests for AI content types."""
from pathlib import Path

from biome_fm.ai.types import FileContent, ImageContent


def test_image_content_frozen():
    ic = ImageContent(data="abc123", media_type="image/png")
    assert ic.data == "abc123"
    assert ic.media_type == "image/png"


def test_file_content_frozen():
    fc = FileContent(path=Path("/tmp/x.py"), content="print('hi')")
    assert fc.path.name == "x.py"
    assert fc.content == "print('hi')"


def test_image_content_default_media_type():
    ic = ImageContent(data="data")
    assert ic.media_type == "image/png"


def test_image_content_is_frozen():
    ic = ImageContent(data="x")
    try:
        ic.data = "y"  # type: ignore
        assert False, "should be frozen"
    except (AttributeError, TypeError):
        pass


def test_file_content_is_frozen():
    fc = FileContent(path=Path("x.py"), content="")
    try:
        fc.content = "y"  # type: ignore
        assert False, "should be frozen"
    except (AttributeError, TypeError):
        pass
