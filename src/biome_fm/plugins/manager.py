"""PluginManager — loads plugins via entry_points, dispatches hooks."""
from __future__ import annotations

import importlib.metadata
import importlib.util
import sys
import warnings
from pathlib import Path

import pluggy

from biome_fm.plugins.hookspecs import BiomeFMSpec


class PluginManager:
    API_VERSION = (1, 0)  # major.minor — increment major on breaking changes

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager("biome_fm")
        self._pm.add_hookspecs(BiomeFMSpec)

    # ── Plugin registration ───────────────────────────────────────────────────

    def register_plugin(self, plugin: object) -> None:
        """Register a plugin object. Skips if API major version mismatches."""
        ver = getattr(plugin, "BIOME_FM_API_VERSION", None)
        if ver is not None and ver[0] != self.API_VERSION[0]:
            warnings.warn(
                f"{plugin!r} requires API v{ver[0]}, app is v{self.API_VERSION[0]} — skipping",
                stacklevel=2,
            )
            return
        self._pm.register(plugin)

    def load_entry_points(self) -> None:
        """Discover and load plugins from 'biome_fm.plugins' entry_points group."""
        for ep in importlib.metadata.entry_points(group="biome_fm.plugins"):
            try:
                plugin_cls = ep.load()
                self.register_plugin(plugin_cls())
            except Exception as exc:
                warnings.warn(f"Failed to load entry point plugin {ep.name!r}: {exc}")

    def load_local_plugins(self, plugin_dir: Path | None = None) -> list[str]:
        """Load .py files from plugin_dir. Each file must define a top-level
        ``Plugin`` class. Returns loaded names. Caller resolves the default path."""
        if plugin_dir is None:
            return []
        if not plugin_dir.exists():
            return []
        loaded: list[str] = []
        candidates = list(plugin_dir.glob("*.py")) + [
            d for d in plugin_dir.iterdir()
            if d.is_dir() and (d / "__init__.py").exists()
        ]
        for path in candidates:
            name = path.stem if path.is_file() else path.name
            mod_name = f"biome_fm_local_{name}"
            try:
                spec = importlib.util.spec_from_file_location(
                    mod_name, path if path.is_file() else path / "__init__.py"
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)  # type: ignore[union-attr]
                    cls = getattr(mod, "Plugin", None)
                    if cls:
                        self.register_plugin(cls())
                        loaded.append(name)
            except Exception as exc:
                warnings.warn(f"Failed to load local plugin {name}: {exc}")
        return loaded

    def get_installed_plugins(self) -> list[dict[str, str]]:
        """Query importlib.metadata for installed biome_fm.plugins entry_points."""
        result: list[dict[str, str]] = []
        for ep in importlib.metadata.entry_points(group="biome_fm.plugins"):
            try:
                meta = importlib.metadata.metadata(ep.dist.name)  # type: ignore[union-attr]
                result.append({
                    "name": ep.dist.name,  # type: ignore[union-attr]
                    "version": ep.dist.version,  # type: ignore[union-attr]
                    "description": meta.get("Summary", ""),
                })
            except Exception:
                pass
        return result

    # ── Hook property ─────────────────────────────────────────────────────────

    @property
    def hook(self) -> pluggy.HookRelay:  # type: ignore[name-defined]
        return self._pm.hook

    # ── Hook delegates ────────────────────────────────────────────────────────

    def call_register_commands(self, registry: object) -> None:
        """Call register_commands historically — late plugins are still invoked."""
        self._pm.hook.register_commands.call_historic(kwargs={"registry": registry})

    def register_commands(self, registry: object) -> None:
        """Backward-compat alias for call_register_commands."""
        self.call_register_commands(registry)

    def on_navigate(self, path: Path) -> None:
        self._pm.hook.on_navigate(path=path)

    def on_file_operation(self, op: str, src: Path, dst: Path | None = None) -> None:
        self._pm.hook.on_file_operation(op=op, src=src, dst=dst)
