"""Per-directory .biome-menu.toml loader with walk-up discovery (F248)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UserMenuItem:
    name: str
    command: str
    shortcut: str = ""


def load_user_menu(cwd: Path, *, global_config: Path | None = None) -> list[UserMenuItem]:
    """Walk up from cwd for .biome-menu.toml; fall back to global config dir."""
    items: list[UserMenuItem] = []
    path = cwd.resolve()
    home = Path.home()
    # Security: only walk up within home to prevent command injection from
    # .biome-menu.toml in untrusted downloaded directories
    try:
        path.relative_to(home)
        within_home = True
    except ValueError:
        within_home = False

    if within_home:
        while True:
            candidate = path / ".biome-menu.toml"
            if candidate.is_file():
                items.extend(_parse(candidate))
                break  # stop at first found; walk-up collects from nearest ancestor only
            parent = path.parent
            if parent == path:
                break
            path = parent

    if not items:
        cfg = global_config if global_config is not None else Path.home() / ".config" / "biome-fm"
        fallback = cfg / "user_menu.toml"
        if fallback.is_file():
            items.extend(_parse(fallback))

    return items


def _parse(path: Path) -> list[UserMenuItem]:
    try:
        data = tomllib.loads(path.read_text())
        return [
            UserMenuItem(
                name=item["name"],
                command=item["command"],
                shortcut=item.get("shortcut", ""),
            )
            for item in data.get("items", [])
            if "name" in item and "command" in item
        ]
    except Exception:
        return []
