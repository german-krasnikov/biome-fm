"""Unit tests for VFS plugin hookspec (F232)."""
from __future__ import annotations

from pathlib import Path

import pluggy

from biome_fm.plugins.hookspecs import BiomeFMSpec
from biome_fm.plugins.manager import PluginManager
from biome_fm.models.vfs_router import VFSRouter

hookimpl = pluggy.HookimplMarker("biome_fm")


def test_hookspec_exists() -> None:
    """provide_vfs must be declared on BiomeFMSpec."""
    assert hasattr(BiomeFMSpec, "provide_vfs")


def test_router_uses_plugin_vfs(tmp_path: Path) -> None:
    """VFSRouter._resolve calls provide_vfs hook and returns plugin VFS for matching path."""

    class FakeVFS:
        def listdir(self, path: Path) -> list:
            return []

    class _Plugin:
        @hookimpl
        def provide_vfs(self, path: str) -> FakeVFS | None:
            if path.startswith("s3://") or path.startswith("s3:/"):
                return FakeVFS()
            return None

    pm = PluginManager()
    pm.register_plugin(_Plugin())
    router = VFSRouter(plugin_manager=pm)

    vfs, _ = router._resolve(Path("s3://my-bucket/prefix"))
    assert isinstance(vfs, FakeVFS)


def test_router_falls_through_for_unhandled_path(tmp_path: Path) -> None:
    """VFSRouter._resolve uses local VFS when no plugin handles the path."""

    class _PassPlugin:
        @hookimpl
        def provide_vfs(self, path: str) -> None:
            return None  # explicitly pass

    (tmp_path / "file.txt").write_text("hi")
    pm = PluginManager()
    pm.register_plugin(_PassPlugin())
    router = VFSRouter(plugin_manager=pm)

    # Should not raise — local VFS handles plain dirs
    items = router.listdir(tmp_path)
    assert any(i.name == "file.txt" for i in items)
