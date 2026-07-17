"""TDD: ShortcutStore — JSON persistence."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.shortcut_store import ShortcutStore


def test_get_default() -> None:
    store = ShortcutStore(Path("/nonexistent/shortcuts.json"))
    assert store.get("copy", "F5") == "F5"


def test_set_overrides() -> None:
    store = ShortcutStore(Path("/nonexistent/shortcuts.json"))
    store.set("copy", "Ctrl+C")
    assert store.get("copy", "F5") == "Ctrl+C"


def test_persist(tmp_path: Path) -> None:
    p = tmp_path / "shortcuts.json"
    store = ShortcutStore(p)
    store.set("delete", "Del")
    store.save()

    store2 = ShortcutStore(p)
    store2.load()
    assert store2.get("delete", "F8") == "Del"


def test_all_returns_dict(tmp_path: Path) -> None:
    store = ShortcutStore(tmp_path / "s.json")
    store.set("copy", "F5")
    store.set("move", "F6")
    d = store.all()
    assert d == {"copy": "F5", "move": "F6"}
