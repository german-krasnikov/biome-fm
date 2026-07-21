"""TDD: F404 Thumbnail Gallery View — tests first, then implementation."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


# ── ThumbnailLoader (pure-Python paths don't need Qt) ──────────────────────


def test_thumbnail_loader_non_image_skipped():
    from biome_fm.views.gallery_view import ThumbnailLoader

    loader = ThumbnailLoader()
    result = loader.request(Path("/tmp/readme.txt"), None)
    assert result is None
    assert Path("/tmp/readme.txt") not in loader._pending


def test_thumbnail_loader_cancel_all():
    from biome_fm.views.gallery_view import ThumbnailLoader

    loader = ThumbnailLoader()
    loader._pending.add(Path("/tmp/fake.png"))
    loader.cancel_all()
    assert not loader._pending


def test_thumbnail_loader_cache(qtbot):
    """Put raw PNG bytes in the queue; drain should populate cache."""
    from biome_fm.views.gallery_view import ThumbnailLoader

    # 1×1 green PNG (minimal valid file)
    PNG_1X1 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    path = Path("/tmp/test.png")
    loader = ThumbnailLoader()
    loader._queue.put((path, PNG_1X1))
    loader._pending.add(path)

    results = loader.drain()
    assert len(results) == 1
    assert results[0][0] == path
    assert path in loader._cache
    assert path not in loader._pending


# ── GalleryView (needs QApplication via qtbot) ─────────────────────────────


def test_gallery_view_set_items_row_count(qtbot):
    from biome_fm.views.gallery_view import GalleryView

    view = GalleryView()
    qtbot.addWidget(view)
    items = [_item("a.txt"), _item("b.png"), _item("folder", is_dir=True)]
    view.set_items(items)
    assert view._model.rowCount() == 3


def test_gallery_view_set_items_clears(qtbot):
    from biome_fm.views.gallery_view import GalleryView

    view = GalleryView()
    qtbot.addWidget(view)
    view.set_items([_item(f"f{i}.txt") for i in range(10)])
    view.set_items([_item(f"g{i}.txt") for i in range(3)])
    assert view._model.rowCount() == 3


def test_gallery_view_current_item(qtbot):
    from biome_fm.views.gallery_view import GalleryView

    view = GalleryView()
    qtbot.addWidget(view)
    items = [_item("alpha.png"), _item("beta.png"), _item("gamma.png")]
    view.set_items(items)
    view._list.setCurrentIndex(view._model.index(1, 0))
    assert view.current_item() == items[1]
