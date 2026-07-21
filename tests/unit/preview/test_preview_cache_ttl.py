"""TTL-aware preview cache tests."""
from pathlib import Path
from unittest.mock import Mock

import biome_fm.preview.presenter as presenter_mod
from biome_fm.models.file_item import FileItem
from biome_fm.preview.presenter import PreviewPresenter, PreviewViewProtocol, _CACHE_TTL
from biome_fm.preview.provider import ContentKind, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


def _item(name: str = "f.md") -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=10, modified=1.0)


def _presenter():
    view = Mock(spec=PreviewViewProtocol)
    view.is_panel_visible.return_value = False
    registry = Mock(spec=PreviewRegistry)
    registry.find.return_value = Mock(
        render=Mock(return_value=PreviewResult(ContentKind.TEXT, "fresh"))
    )
    return PreviewPresenter(view, registry), view, registry


def test_cache_hit_within_ttl():
    """Cache hit within TTL → show_result immediately, no provider call."""
    p, view, registry = _presenter()
    item = _item()
    cached = PreviewResult(ContentKind.HTML, "<cached>")
    # Store with a timestamp that is NOT expired (now)
    import time
    p._cache[(item.path, item.modified, p._dark)] = (cached, time.monotonic())

    p._render_item(item)

    view.show_result.assert_called_once_with(cached)
    view.set_busy.assert_not_called()
    registry.find.assert_not_called()


def test_cache_expired_after_ttl(monkeypatch):
    """Cache entry older than TTL → re-render, provider called again."""
    p, view, registry = _presenter()
    item = _item()
    old_result = PreviewResult(ContentKind.HTML, "<stale>")
    # Store with timestamp 0 (epoch) — guaranteed expired
    p._cache[(item.path, item.modified, p._dark)] = (old_result, 0.0)

    # Monkeypatch monotonic to return a value well past TTL
    monkeypatch.setattr(presenter_mod.time, "monotonic", lambda: _CACHE_TTL + 1.0)

    p._render_item(item)

    # Must NOT have served the stale cache entry
    view.show_result.assert_not_called()
    view.set_busy.assert_called_once_with(True)


def test_cache_eviction_at_max():
    """64-entry FIFO eviction still works with tuple-valued cache."""
    p, view, _ = _presenter()
    import time
    ts = time.monotonic()
    # Fill to max
    for i in range(p._CACHE_MAX):
        key = (Path(f"/tmp/{i}.txt"), float(i), True)
        p._cache[key] = (PreviewResult(ContentKind.TEXT, str(i)), ts)

    first_key = next(iter(p._cache))

    # Simulate _run storing one more entry (triggers eviction)
    with p._cache_lock:
        if len(p._cache) >= p._CACHE_MAX:
            p._cache.pop(next(iter(p._cache)))
        p._cache[(Path("/tmp/new.txt"), 99.0, True)] = (
            PreviewResult(ContentKind.TEXT, "new"), ts
        )

    assert first_key not in p._cache
    assert len(p._cache) == p._CACHE_MAX
