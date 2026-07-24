"""Unit tests for PreviewPresenter — fully Qt-free."""
from pathlib import Path
from unittest.mock import Mock

from biome_fm.models.file_item import FileItem
from biome_fm.preview.presenter import PreviewPresenter, PreviewViewProtocol
from biome_fm.preview.provider import ContentKind, PreviewMode, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


def _make_item(name: str = "test.md", modified: float = 1.0) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=10, modified=modified)


def _make_presenter(is_visible: bool = False):
    view = Mock(spec=PreviewViewProtocol)
    view.is_panel_visible.return_value = is_visible
    registry = Mock(spec=PreviewRegistry)
    registry.find.return_value = Mock(
        render=Mock(return_value=PreviewResult(ContentKind.HTML, "<p>ok</p>"))
    )
    return PreviewPresenter(view, registry), view


def test_toggle_opens_when_hidden():
    presenter, view = _make_presenter(is_visible=False)
    presenter.toggle_item(_make_item())
    view.set_visible.assert_called_with(True)


def test_toggle_closes_same_file():
    presenter, view = _make_presenter(is_visible=True)
    item = _make_item()
    presenter._current = item.path
    presenter.toggle_item(item)
    view.set_visible.assert_called_with(False)


def test_toggle_skips_dotdot():
    presenter, view = _make_presenter(is_visible=False)
    item = FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0)
    presenter.toggle_item(item)
    view.set_visible.assert_not_called()


def test_toggle_skips_none():
    presenter, view = _make_presenter(is_visible=False)
    presenter.toggle_item(None)
    view.set_visible.assert_not_called()


def test_update_if_visible_noop_when_hidden():
    presenter, view = _make_presenter(is_visible=False)
    presenter.update_if_visible(_make_item())
    view.set_busy.assert_not_called()


def test_update_if_visible_noop_same_file():
    presenter, view = _make_presenter(is_visible=True)
    item = _make_item()
    presenter._current = item.path
    presenter.update_if_visible(item)
    view.set_busy.assert_not_called()


def test_update_if_visible_noop_none():
    presenter, view = _make_presenter(is_visible=True)
    presenter.update_if_visible(None)
    view.set_busy.assert_not_called()


def test_cache_hit_skips_thread():
    import time
    presenter, view = _make_presenter(is_visible=False)
    item = _make_item()
    cached = PreviewResult(ContentKind.HTML, "<p>cached</p>")
    presenter._cache[(item.path, item.modified, presenter._dark, PreviewMode.AUTO)] = (cached, time.monotonic())
    presenter.toggle_item(item)
    view.show_result.assert_called_once_with(cached)
    view.set_busy.assert_not_called()


def test_drain_delivers_result():
    presenter, view = _make_presenter(is_visible=True)
    result = PreviewResult(ContentKind.TEXT, "hello")
    presenter._queue.put(result)
    presenter.drain()
    view.set_busy.assert_called_with(False)
    view.show_result.assert_called_with(result)


def test_drain_empty_no_crash():
    presenter, view = _make_presenter()
    presenter.drain()  # should not raise


def test_shutdown():
    presenter, _ = _make_presenter()
    presenter.shutdown()  # should not raise


def test_toggle_new_file_when_visible():
    presenter, view = _make_presenter(is_visible=True)
    item1 = _make_item("a.md")
    item2 = _make_item("b.md")
    presenter._current = item1.path
    presenter.toggle_item(item2)
    view.set_busy.assert_called_with(True)


def test_render_item_queues_render():
    presenter, view = _make_presenter(is_visible=False)
    presenter.render_item(_make_item())
    view.set_busy.assert_called_with(True)
    view.set_visible.assert_not_called()


def test_render_item_skips_none():
    presenter, view = _make_presenter()
    presenter.render_item(None)
    view.set_busy.assert_not_called()


def test_render_item_skips_dotdot():
    presenter, view = _make_presenter()
    item = FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0)
    presenter.render_item(item)
    view.set_busy.assert_not_called()


def test_cache_has_lock():
    """I13: PreviewPresenter must have a _cache_lock for thread-safety."""
    import threading
    presenter, _ = _make_presenter()
    assert hasattr(presenter, "_cache_lock")
    assert isinstance(presenter._cache_lock, type(threading.Lock()))


# ── Item-7: explicit modes bypass registry, AUTO delegates to it ─────────────

def test_git_blame_mode_bypasses_registry():
    from biome_fm.preview.provider import PreviewMode
    from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
    presenter, _ = _make_presenter()
    presenter._forced_mode = PreviewMode.GIT_BLAME
    assert isinstance(presenter._get_provider(Path("/some/file.py")), GitBlamePreviewProvider)


def test_git_log_mode_bypasses_registry():
    from biome_fm.preview.provider import PreviewMode
    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    presenter, _ = _make_presenter()
    presenter._forced_mode = PreviewMode.GIT_LOG
    assert isinstance(presenter._get_provider(Path("/some/file.py")), GitLogPreviewProvider)


def test_auto_mode_delegates_to_registry():
    from biome_fm.preview.provider import PreviewMode
    from biome_fm.preview.providers.code import CodePreviewProvider
    presenter, _ = _make_presenter()
    presenter._registry.find.return_value = CodePreviewProvider()
    presenter._forced_mode = PreviewMode.AUTO
    item = _make_item("script.py")
    result = presenter._get_provider(item.path, item)
    presenter._registry.find.assert_called_once_with(item.path)
    assert isinstance(result, CodePreviewProvider)


# ── Item-10: mode in cache key ────────────────────────────────────────────────

def test_mode_switch_busts_cache():
    """AUTO cache entry is not served when mode switches to GIT_BLAME."""
    import time
    from biome_fm.preview.provider import PreviewMode
    presenter, view = _make_presenter()
    item = _make_item()
    cached = PreviewResult(ContentKind.HTML, "<cached>")
    # Prime cache under AUTO key
    presenter._cache[(item.path, item.modified, presenter._dark, PreviewMode.AUTO)] = (
        cached, time.monotonic()
    )
    # Switch to GIT_BLAME — should miss cache
    presenter._forced_mode = PreviewMode.GIT_BLAME
    presenter._render_item(item)
    view.set_busy.assert_called_once_with(True)
    view.show_result.assert_not_called()


def test_same_mode_reuses_cache():
    """Same mode key → cache hit, show_result immediately, no set_busy."""
    import time
    from biome_fm.preview.provider import PreviewMode
    presenter, view = _make_presenter()
    item = _make_item()
    cached = PreviewResult(ContentKind.HTML, "<cached>")
    presenter._cache[(item.path, item.modified, presenter._dark, PreviewMode.AUTO)] = (
        cached, time.monotonic()
    )
    presenter._render_item(item)  # _forced_mode is AUTO by default
    view.show_result.assert_called_once_with(cached)
    view.set_busy.assert_not_called()


def test_race_guard_discards_stale_mode_result():
    """_run does NOT enqueue result when mode changed since submission."""
    from biome_fm.preview.provider import PreviewMode, PreviewRequest
    presenter, view = _make_presenter()
    item = _make_item()
    presenter._current = item.path
    req = PreviewRequest(path=item.path, dark=presenter._dark)
    cache_key = (item.path, item.modified, presenter._dark, PreviewMode.AUTO)
    fake_result = PreviewResult(ContentKind.TEXT, "auto render")
    fake_provider = Mock(render=Mock(return_value=fake_result))

    # Flip mode to HEX BEFORE _run executes (simulates race)
    presenter._forced_mode = PreviewMode.HEX

    # Call _run synchronously with mode_at_submit=AUTO — guard should block enqueue
    presenter._run(fake_provider, req, cache_key, PreviewMode.AUTO)

    assert presenter._queue.empty()
