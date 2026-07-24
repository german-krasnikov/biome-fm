"""Sprint 3 architecture improvement tests."""
from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# #33 VFS Protocol split
# ---------------------------------------------------------------------------

def test_archive_vfs_is_readable_not_writable():
    from biome_fm.models.vfs import ReadableVFS, WritableVFS
    from biome_fm.models.archive_vfs import ArchiveVFS
    vfs = ArchiveVFS(Path("fake.zip"))
    assert isinstance(vfs, ReadableVFS)
    assert not isinstance(vfs, WritableVFS)


def test_local_vfs_is_writable():
    from biome_fm.models.vfs import WritableVFS, ReadableVFS, LocalVFS
    vfs = LocalVFS()
    assert isinstance(vfs, WritableVFS)
    assert isinstance(vfs, ReadableVFS)


def test_vfs_protocol_alias_is_writable():
    from biome_fm.models.vfs import VFSProtocol, WritableVFS
    assert VFSProtocol is WritableVFS


def test_router_raises_on_readonly_delete(tmp_path):
    import zipfile as _zf
    from biome_fm.models.vfs import VFSReadOnlyError
    from biome_fm.models.vfs_router import VFSRouter

    z = tmp_path / "a.zip"
    with _zf.ZipFile(z, "w") as zf:
        zf.writestr("file.txt", "data")

    router = VFSRouter()
    with pytest.raises(VFSReadOnlyError):
        router.delete(z / "file.txt")


def test_router_raises_on_readonly_move(tmp_path):
    import zipfile as _zf
    from biome_fm.models.vfs import VFSReadOnlyError
    from biome_fm.models.vfs_router import VFSRouter

    z = tmp_path / "a.zip"
    with _zf.ZipFile(z, "w") as zf:
        zf.writestr("file.txt", "data")

    router = VFSRouter()
    with pytest.raises(VFSReadOnlyError):
        router.move(z / "file.txt", tmp_path / "out.txt")


def test_router_raises_on_readonly_mkdir(tmp_path):
    import zipfile as _zf
    from biome_fm.models.vfs import VFSReadOnlyError
    from biome_fm.models.vfs_router import VFSRouter

    z = tmp_path / "a.zip"
    with _zf.ZipFile(z, "w") as zf:
        zf.writestr("file.txt", "data")

    router = VFSRouter()
    with pytest.raises(VFSReadOnlyError):
        router.mkdir(z / "newdir")


def test_router_copy_from_archive_extracts(tmp_path):
    import zipfile as _zf
    from biome_fm.models.vfs_router import VFSRouter

    z = tmp_path / "a.zip"
    with _zf.ZipFile(z, "w") as zf:
        zf.writestr("hello.txt", "world")

    router = VFSRouter()
    dst = tmp_path / "out.txt"
    router.copy(z / "hello.txt", dst)
    assert dst.read_text() == "world"


# ---------------------------------------------------------------------------
# #43 _store_base atomic write/read
# ---------------------------------------------------------------------------

def test_atomic_write_json_roundtrip(tmp_path):
    from biome_fm.models._store_base import atomic_write_json, read_json
    p = tmp_path / "data.json"
    atomic_write_json(p, {"key": "value"})
    assert read_json(p) == {"key": "value"}


def test_atomic_write_creates_parent(tmp_path):
    from biome_fm.models._store_base import atomic_write_json
    p = tmp_path / "nested" / "dir" / "data.json"
    atomic_write_json(p, {})
    assert p.exists()


def test_read_json_missing_returns_empty_dict(tmp_path):
    from biome_fm.models._store_base import read_json
    assert read_json(tmp_path / "nonexistent.json") == {}


def test_read_json_corrupt_returns_empty_dict(tmp_path):
    from biome_fm.models._store_base import read_json
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert read_json(p) == {}


def test_read_json_custom_default(tmp_path):
    from biome_fm.models._store_base import read_json
    assert read_json(tmp_path / "none.json", default=[]) == []


# ---------------------------------------------------------------------------
# #50 RichPaneViewProtocol
# ---------------------------------------------------------------------------

def test_rich_pane_view_protocol_defined():
    from biome_fm.presenters.pane_presenter import PaneViewProtocol, RichPaneViewProtocol
    # RichPaneViewProtocol inherits from PaneViewProtocol
    assert PaneViewProtocol in RichPaneViewProtocol.__bases__


# ---------------------------------------------------------------------------
# #51 AIProviderProtocol
# ---------------------------------------------------------------------------

def test_noop_provider_satisfies_protocol():
    from biome_fm.ai.provider import AIProviderProtocol, NoOpProvider
    assert isinstance(NoOpProvider(), AIProviderProtocol)


def test_noop_terminate_is_safe():
    from biome_fm.ai.provider import NoOpProvider
    NoOpProvider().terminate()  # must not raise


def test_noop_chat_stream_events_returns_empty():
    from biome_fm.ai.provider import NoOpProvider
    assert list(NoOpProvider().chat_stream_events([])) == []


# ---------------------------------------------------------------------------
# #54 TOML escaping
# ---------------------------------------------------------------------------

def test_command_store_roundtrip_with_quotes(tmp_path):
    from biome_fm.models.command_store import CommandStore, UserCommand

    store = CommandStore(tmp_path / "cmds.toml")
    store.add(UserCommand(
        id='id"with"quotes',
        label='echo "hello"',
        command='bash -c "echo hello"',
        shortcut='',
    ))
    store.save()

    store2 = CommandStore(tmp_path / "cmds.toml")
    assert store2.commands[0].label == 'echo "hello"'
    assert store2.commands[0].command == 'bash -c "echo hello"'
    assert store2.commands[0].id == 'id"with"quotes'


def test_command_store_backslash_roundtrip(tmp_path):
    from biome_fm.models.command_store import CommandStore, UserCommand

    store = CommandStore(tmp_path / "cmds.toml")
    store.add(UserCommand(id="x", label="test\\back", command="cmd\\path", shortcut=""))
    store.save()
    store2 = CommandStore(tmp_path / "cmds.toml")
    assert store2.commands[0].label == "test\\back"
    assert store2.commands[0].command == "cmd\\path"


def test_command_store_newline_roundtrip(tmp_path):
    from biome_fm.models.command_store import CommandStore, UserCommand

    store = CommandStore(tmp_path / "cmds.toml")
    store.add(UserCommand(id="nl", label="multi", command="echo hello\nworld", shortcut=""))
    store.save()
    store2 = CommandStore(tmp_path / "cmds.toml")
    assert store2.commands[0].command == "echo hello\nworld"


def test_toml_escape_covers_control_chars():
    from biome_fm.models._store_base import toml_escape
    assert "\\n" in toml_escape("a\nb")
    assert "\\r" in toml_escape("a\rb")
    assert "\\t" in toml_escape("a\tb")
    assert '\\"' in toml_escape('a"b')


def test_tag_store_path_with_quotes(tmp_path):
    from biome_fm.models.tag_store import TagStore

    store = TagStore.load(tmp_path / "tags.toml")
    p = Path('/path/with"quote/file.txt')
    store.set_tags(p, ["important"])
    store.save()

    store2 = TagStore.load(tmp_path / "tags.toml")
    assert store2.get_tags(p) == ["important"]


# ---------------------------------------------------------------------------
# #56 Signal disconnect tracking
# ---------------------------------------------------------------------------

def test_macro_store_corrupt_json(tmp_path):
    from biome_fm.models.macro_store import MacroStore
    p = tmp_path / "macros.json"
    p.write_text("CORRUPT{{{")
    store = MacroStore(p)
    store.load()
    assert store.list_macros() == []


def test_shortcut_store_corrupt_json(tmp_path):
    from biome_fm.models.shortcut_store import ShortcutStore
    p = tmp_path / "shortcuts.json"
    p.write_text("NOT JSON")
    store = ShortcutStore(p)
    store.load()
    assert store.all() == {}


def test_cleanup_cancels_background_thread():
    from biome_fm.presenters.pane_presenter import PanePresenter

    class _View:
        def set_items(self, items, **kw): pass
        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, p): pass
        def current_cursor_item(self): return None
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, p): pass
        def select_item(self, n): pass
        def set_dir_size(self, p, s): pass

    from biome_fm.models.vfs import LocalVFS
    presenter = PanePresenter(_View(), LocalVFS())
    presenter.cleanup()
    assert presenter._size_cancel[0] is True


def test_cleanup_is_idempotent():
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.vfs import LocalVFS

    class _View:
        def set_items(self, items, **kw): pass
        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, p): pass
        def current_cursor_item(self): return None
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, p): pass
        def select_item(self, n): pass
        def set_dir_size(self, p, s): pass

    presenter = PanePresenter(_View(), LocalVFS())
    presenter.cleanup()
    presenter.cleanup()  # must not raise


# ---------------------------------------------------------------------------
# #62 Config validation
# ---------------------------------------------------------------------------

def test_glass_opacity_clamped_low():
    from biome_fm.config import Config
    assert Config(glass_opacity=-10).glass_opacity == 0


def test_glass_opacity_clamped_high():
    from biome_fm.config import Config
    assert Config(glass_opacity=200).glass_opacity == 100


def test_glass_opacity_invalid_type_uses_default():
    from biome_fm.config import Config
    assert Config(glass_opacity="high").glass_opacity == 47  # type: ignore[arg-type]


def test_ui_font_size_clamped():
    from biome_fm.config import Config
    assert Config(ui_font_size=9999).ui_font_size == 72
    assert Config(ui_font_size=-1).ui_font_size == 0


def test_ui_font_size_invalid_type_uses_default():
    from biome_fm.config import Config
    assert Config(ui_font_size="large").ui_font_size == 0  # type: ignore[arg-type]


def test_splitter_sizes_reset_wrong_length():
    from biome_fm.config import Config
    assert Config(splitter_sizes=[100]).splitter_sizes == [600, 600]


def test_splitter_sizes_reset_not_list():
    from biome_fm.config import Config
    assert Config(splitter_sizes="bad").splitter_sizes == [600, 600]  # type: ignore[arg-type]


def test_splitter_sizes_negative_clamped():
    from biome_fm.config import Config
    c = Config(splitter_sizes=[-10, 500])
    assert c.splitter_sizes[0] == 1


def test_recent_dirs_reset_when_not_list():
    from biome_fm.config import Config
    assert Config(recent_dirs="path").recent_dirs == []  # type: ignore[arg-type]


def test_theme_reset_when_not_string():
    from biome_fm.config import Config
    assert Config(theme=42).theme == "dark"  # type: ignore[arg-type]


def test_valid_config_passes_through():
    from biome_fm.config import Config
    c = Config(glass_opacity=50, ui_font_size=12, splitter_sizes=[400, 800])
    assert c.glass_opacity == 50
    assert c.ui_font_size == 12
    assert c.splitter_sizes == [400, 800]


def test_load_config_corrupt_values(tmp_path):
    from biome_fm.config import load_config
    p = tmp_path / "config.toml"
    p.write_text('glass_opacity = "high"\nui_font_size = -5\nsplitter_sizes = []\n')
    c = load_config(p)
    assert c.glass_opacity == 47  # default (invalid string → fallback)
    assert c.ui_font_size == 0
    assert c.splitter_sizes == [600, 600]
