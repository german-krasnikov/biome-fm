"""Unit tests for F419 — provide_preview_providers hookspec."""
from __future__ import annotations

import pluggy

from biome_fm.plugins.hookspecs import BiomeFMSpec, hookimpl
from biome_fm.plugins.manager import PluginManager


def test_hookspec_exists() -> None:
    assert hasattr(BiomeFMSpec, "provide_preview_providers")


def test_single_plugin_returns_providers() -> None:
    provider = object()

    class MyPlugin:
        @hookimpl
        def provide_preview_providers(self) -> list[object]:
            return [provider]

    pm = PluginManager()
    pm.register_plugin(MyPlugin())
    assert pm.get_preview_providers() == [provider]


def test_multiple_plugins_flattened() -> None:
    p1, p2 = object(), object()

    class PluginA:
        @hookimpl
        def provide_preview_providers(self) -> list[object]:
            return [p1]

    class PluginB:
        @hookimpl
        def provide_preview_providers(self) -> list[object]:
            return [p2]

    pm = PluginManager()
    pm.register_plugin(PluginA())
    pm.register_plugin(PluginB())
    result = pm.get_preview_providers()
    assert p1 in result and p2 in result
    assert len(result) == 2


def test_no_plugins_returns_empty() -> None:
    pm = PluginManager()
    assert pm.get_preview_providers() == []
