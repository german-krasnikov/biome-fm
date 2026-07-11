"""Unit tests for PluginManager — no Qt required."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.plugins.hookspecs import hookimpl
from biome_fm.plugins.manager import PluginManager


class _TestPlugin:
    """Stub plugin implementing all hooks."""

    def __init__(self) -> None:
        self.navigated: list[Path] = []
        self.ops: list[tuple[str, Path, Path | None]] = []
        self.registered = False

    @hookimpl
    def register_commands(self, registry: object) -> None:
        self.registered = True

    @hookimpl
    def on_navigate(self, path: Path) -> None:
        self.navigated.append(path)

    @hookimpl
    def on_file_operation(self, op: str, src: Path, dst: Path | None) -> None:
        self.ops.append((op, src, dst))


class _NavOnlyPlugin:
    """Plugin implementing only on_navigate."""

    def __init__(self) -> None:
        self.navigated: list[Path] = []

    @hookimpl
    def on_navigate(self, path: Path) -> None:
        self.navigated.append(path)


def _pm_with(*plugins: object) -> PluginManager:
    pm = PluginManager()
    for p in plugins:
        pm.register_plugin(p)
    return pm


def test_register_commands_calls_plugin() -> None:
    plugin = _TestPlugin()
    pm = _pm_with(plugin)
    pm.register_commands(registry=object())
    assert plugin.registered is True


def test_on_navigate_calls_plugin() -> None:
    plugin = _TestPlugin()
    pm = _pm_with(plugin)
    pm.on_navigate(Path("/tmp"))
    assert plugin.navigated == [Path("/tmp")]


def test_on_file_operation_calls_plugin() -> None:
    plugin = _TestPlugin()
    pm = _pm_with(plugin)
    src, dst = Path("/a"), Path("/b")
    pm.on_file_operation("copy", src, dst)
    assert plugin.ops == [("copy", src, dst)]


def test_multiple_plugins() -> None:
    p1, p2 = _TestPlugin(), _TestPlugin()
    pm = _pm_with(p1, p2)
    pm.on_navigate(Path("/x"))
    assert p1.navigated == [Path("/x")]
    assert p2.navigated == [Path("/x")]


def test_register_plugin_directly() -> None:
    pm = PluginManager()
    plugin = _TestPlugin()
    pm.register_plugin(plugin)
    pm.on_navigate(Path("/direct"))
    assert plugin.navigated == [Path("/direct")]


def test_partial_plugin_ok() -> None:
    plugin = _NavOnlyPlugin()
    pm = _pm_with(plugin)
    pm.register_commands(registry=object())  # should not crash
    pm.on_navigate(Path("/partial"))
    assert plugin.navigated == [Path("/partial")]


def test_broken_entry_point_skipped() -> None:
    pm = PluginManager()
    bad_ep = MagicMock()
    bad_ep.load.side_effect = ImportError("broken")
    with patch("importlib.metadata.entry_points", return_value=[bad_ep]):
        pm.load_entry_points()  # must not raise
