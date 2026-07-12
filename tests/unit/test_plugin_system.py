"""Unit tests for Phase 3 plugin system — no Qt required."""
from __future__ import annotations

import warnings
from pathlib import Path

import pluggy

from biome_fm.plugins.hookspecs import BiomeFMSpec, hookimpl
from biome_fm.plugins.manager import PluginManager
from biome_fm.plugins.theme_registry import ThemeRegistry
from biome_fm.plugins.types import ActionSpec, ColumnDef

# ── ThemeRegistry ─────────────────────────────────────────────────────────────

def test_theme_registry_fallback() -> None:
    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    tokens = ThemeRegistry(pm).resolve("nonexistent")
    assert tokens["base"] == "#1c1c1e"
    assert "text" in tokens


def test_theme_plugin_partial_override() -> None:
    class FakeTheme:
        @hookimpl
        def provide_theme(self, name: str):  # type: ignore[override]
            return {"base": "#ff0000"} if name == "red" else None

    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    pm.register(FakeTheme())
    tokens = ThemeRegistry(pm).resolve("red")
    assert tokens["base"] == "#ff0000"
    assert "text" in tokens  # merged from fallback


# ── Historic register_commands ────────────────────────────────────────────────

def test_register_commands_historic() -> None:
    called: list[object] = []

    class LatePlugin:
        @hookimpl
        def register_commands(self, registry: object) -> None:
            called.append(registry)

    pm_obj = PluginManager()
    registry = object()
    pm_obj.call_register_commands(registry)   # fire historic
    pm_obj.register_plugin(LatePlugin())      # register AFTER
    assert registry in called                  # still called via historic


# ── API version gate ──────────────────────────────────────────────────────────

def test_api_version_mismatch_skipped() -> None:
    class BadPlugin:
        BIOME_FM_API_VERSION = (99, 0)

        @hookimpl
        def on_navigate(self, path: Path) -> None:
            raise AssertionError("should never be called")

    pm_obj = PluginManager()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pm_obj.register_plugin(BadPlugin())
    assert len(w) == 1
    assert "skipping" in str(w[0].message).lower()
    # verify BadPlugin was NOT registered
    registered = list(pm_obj._pm.get_plugins())
    assert not any(isinstance(p, BadPlugin) for p in registered)
    # verify hook doesn't fire (would raise if plugin were registered)
    pm_obj.on_navigate(Path("/x"))  # must not raise


def test_api_version_compatible() -> None:
    """Minor version mismatch (1, 5) vs (1, 0) is accepted."""
    called: list[Path] = []

    class CompatPlugin:
        BIOME_FM_API_VERSION = (1, 5)

        @hookimpl
        def on_navigate(self, path: Path) -> None:
            called.append(path)

    pm_obj = PluginManager()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pm_obj.register_plugin(CompatPlugin())
    assert len(w) == 0
    pm_obj.on_navigate(Path("/ok"))
    assert Path("/ok") in called


# ── before_file_operation veto ────────────────────────────────────────────────

def test_before_op_veto() -> None:
    class VetoPlugin:
        @hookimpl
        def before_file_operation(self, op: str, src: Path, dst: object) -> bool | None:
            return False if op == "delete" else None

    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    pm.register(VetoPlugin())
    result = pm.hook.before_file_operation(op="delete", src=Path("/a"), dst=None)
    assert result is False


def test_before_op_allow() -> None:
    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    # no plugins — allow
    result = pm.hook.before_file_operation(op="delete", src=Path("/a"), dst=None)
    assert result is None


# ── extra_archive_extensions ──────────────────────────────────────────────────

def test_extra_extensions() -> None:
    class RarPlugin:
        @hookimpl
        def extra_archive_extensions(self) -> list[str]:
            return ["rar", "7z"]

    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    pm.register(RarPlugin())
    all_ext: list[str] = []
    for lst in pm.hook.extra_archive_extensions():
        all_ext.extend(lst)
    assert "rar" in all_ext and "7z" in all_ext


# ── context_menu_actions ──────────────────────────────────────────────────────

def test_context_menu_actions() -> None:
    class MenuPlugin:
        @hookimpl
        def context_menu_actions(self, items: list[object], pane_id: str) -> list[ActionSpec]:
            return [ActionSpec(label="Test", callback=lambda: None)]

    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    pm.register(MenuPlugin())
    results = pm.hook.context_menu_actions(items=[], pane_id="left")
    # results is list of lists (one per plugin)
    flat = [a for lst in results for a in lst]
    assert any(a.label == "Test" for a in flat)


# ── load_local_plugins ────────────────────────────────────────────────────────

def test_load_local_plugin(tmp_path: Path) -> None:
    (tmp_path / "myplugin.py").write_text(
        "from biome_fm.plugins.hookspecs import hookimpl\n"
        "class Plugin:\n"
        "    @hookimpl\n"
        "    def on_navigate(self, path): pass\n"
    )
    pm_obj = PluginManager()
    loaded = pm_obj.load_local_plugins(tmp_path)
    assert "myplugin" in loaded


def test_load_local_plugin_no_Plugin_class(tmp_path: Path) -> None:
    (tmp_path / "noplugin.py").write_text("X = 1\n")
    pm_obj = PluginManager()
    loaded = pm_obj.load_local_plugins(tmp_path)
    assert loaded == []


def test_load_local_plugins_missing_dir(tmp_path: Path) -> None:
    pm_obj = PluginManager()
    loaded = pm_obj.load_local_plugins(tmp_path / "nonexistent")
    assert loaded == []


# ── ActionSpec / ColumnDef types ──────────────────────────────────────────────

def test_action_spec_defaults() -> None:
    a = ActionSpec(label="X", callback=lambda: None)
    assert a.shortcut == ""
    assert a.icon_name == ""
    assert a.separator_before is False


def test_column_def_defaults() -> None:
    c = ColumnDef(id="git.status", title="Git")
    assert c.width == 80
    assert c.alignment == "left"


# ── hook property ─────────────────────────────────────────────────────────────

def test_hook_property() -> None:
    pm_obj = PluginManager()
    # hook property exposes raw HookRelay
    assert pm_obj.hook is pm_obj._pm.hook


# ── extra_columns hookspec exists ─────────────────────────────────────────────

def test_extra_columns_hookspec() -> None:
    class ColPlugin:
        @hookimpl
        def extra_columns(self) -> list[ColumnDef]:
            return [ColumnDef(id="x", title="X")]

    pm = pluggy.PluginManager("biome_fm")
    pm.add_hookspecs(BiomeFMSpec)
    pm.register(ColPlugin())
    results = pm.hook.extra_columns()
    flat = [c for lst in results for c in lst]
    assert any(c.id == "x" for c in flat)
