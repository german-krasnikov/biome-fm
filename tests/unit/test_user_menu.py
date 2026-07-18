"""Unit tests for user_menu loader (F248)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.user_menu import UserMenuItem, load_user_menu


def _write_menu(path: Path, items: list[dict]) -> None:
    lines = []
    for item in items:
        lines.append("[[items]]")
        lines.append(f'name = "{item["name"]}"')
        lines.append(f'command = "{item["command"]}"')
        if "shortcut" in item:
            lines.append(f'shortcut = "{item["shortcut"]}"')
        lines.append("")
    path.write_text("\n".join(lines))


def test_load_from_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    _write_menu(tmp_path / ".biome-menu.toml", [
        {"name": "Run tests", "command": "pytest $d"},
        {"name": "Git status", "command": "git status", "shortcut": "g"},
    ])
    items = load_user_menu(tmp_path, global_config=tmp_path / "nowhere")
    assert len(items) == 2
    assert items[0].name == "Run tests"
    assert items[0].command == "pytest $d"
    assert items[0].shortcut == ""
    assert items[1].name == "Git status"
    assert items[1].shortcut == "g"


def test_walk_up_finds_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    _write_menu(tmp_path / ".biome-menu.toml", [{"name": "Parent", "command": "ls"}])
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    items = load_user_menu(sub, global_config=tmp_path / "nowhere")
    assert any(i.name == "Parent" for i in items)


def test_no_walkup_outside_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Walk-up is skipped when cwd is not under home — falls back to global config."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    outside = tmp_path / "downloads" / "project"
    outside.mkdir(parents=True)
    _write_menu(outside / ".biome-menu.toml", [{"name": "Injected", "command": "rm -rf /"}])
    items = load_user_menu(outside, global_config=tmp_path / "nowhere")
    assert items == []


def test_fallback_to_global(tmp_path: Path) -> None:
    global_dir = tmp_path / "config"
    global_dir.mkdir()
    _write_menu(global_dir / "user_menu.toml", [{"name": "Global", "command": "echo hi"}])
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    items = load_user_menu(empty_dir, global_config=global_dir)
    assert any(i.name == "Global" for i in items)


def test_empty_file(tmp_path: Path) -> None:
    (tmp_path / ".biome-menu.toml").write_text("")
    items = load_user_menu(tmp_path, global_config=tmp_path / "nowhere")
    assert items == []


def test_missing_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    items = load_user_menu(empty, global_config=tmp_path / "nowhere")
    assert items == []


def test_malformed_toml_ignored(tmp_path: Path) -> None:
    (tmp_path / ".biome-menu.toml").write_text("NOT VALID TOML ::::")
    items = load_user_menu(tmp_path, global_config=tmp_path / "nowhere")
    assert items == []
