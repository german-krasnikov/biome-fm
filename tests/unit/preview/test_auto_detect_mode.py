"""Unit tests for PreviewPresenter._auto_detect_mode (F218)."""
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.preview.presenter import PreviewPresenter


def _presenter() -> PreviewPresenter:
    return PreviewPresenter.__new__(PreviewPresenter)


def _item(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=False, size=path.stat().st_size, modified=0.0)


def test_binary_detected_as_hex(tmp_path: Path) -> None:
    f = tmp_path / "test.bin"
    # Lots of C0 control chars (0-8 range) → >30% non-printable triggers hex
    f.write_bytes(bytes([0, 1, 2, 3, 4, 5, 6, 7, 8] * 40 + list(b"hello")))
    assert _presenter()._auto_detect_mode(_item(f)) == "hex"


def test_text_detected_as_text(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("hello world\n" * 20)
    assert _presenter()._auto_detect_mode(_item(f)) == "text"


def test_empty_file_returns_text(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    item = FileItem(name="empty.txt", path=f, is_dir=False, size=0, modified=0.0)
    assert _presenter()._auto_detect_mode(item) == "text"
