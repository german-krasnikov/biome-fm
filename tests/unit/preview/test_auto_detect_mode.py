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


def test_auto_detect_bounded_read(tmp_path: Path, monkeypatch) -> None:
    f = tmp_path / "large.bin"
    f.write_bytes(b"A" * 2_000_000)  # 2 MB, all printable → "text"
    item = FileItem(name=f.name, path=f, is_dir=False, size=2_000_000, modified=0.0)

    def _no_full_read(self):
        raise AssertionError("read_bytes() must not be called — use open().read(n)")

    monkeypatch.setattr(Path, "read_bytes", _no_full_read)

    p = PreviewPresenter.__new__(PreviewPresenter)
    # RED: raises AssertionError because read_bytes() is called
    # GREEN: uses open("rb").read(512), never calls read_bytes()
    result = p._auto_detect_mode(item)
    assert result in ("text", "hex")
