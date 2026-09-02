"""Unit tests for ImagePreviewProvider EXIF overlay (F317)."""
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.image import ImagePreviewProvider, _read_exif


def test_exif_returns_none_for_non_jpeg(tmp_path: Path) -> None:
    f = tmp_path / "test.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    assert _read_exif(f) is None


def test_exif_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _read_exif(tmp_path / "ghost.jpg") is None


def test_exif_html_escapes_values(tmp_path: Path) -> None:
    from biome_fm.preview.providers.image import _exif_html
    p = tmp_path / "test.jpg"
    p.write_bytes(b"\xff\xd8" + b"\x00" * 4)
    result = _exif_html(p, b"\xff\xd8", {"Make": "<Canon>", "Model": "5D & Mark IV"})
    assert "<Canon>" not in result
    assert "&lt;Canon&gt;" in result
    assert "5D &amp; Mark IV" in result


def test_render_without_exif_returns_image_kind(tmp_path: Path) -> None:
    """PNG has no EXIF → unchanged IMAGE result."""
    f = tmp_path / "test.png"
    # minimal valid-looking PNG (8-byte magic + empty body; Qt won't display it but render() doesn't validate)
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    provider = ImagePreviewProvider()
    req = PreviewRequest(path=f)
    result = provider.render(req)
    assert result.kind == ContentKind.IMAGE
