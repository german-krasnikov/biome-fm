"""Tests for config.py — TOML persistence."""
from __future__ import annotations

from pathlib import Path

from biome_fm.config import Config, load_config, save_config


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg == Config()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(theme="light"), p)
    assert load_config(p).theme == "light"


def test_partial_toml_merges_defaults(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('theme = "solarized"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.theme == "solarized"
    assert cfg.splitter_sizes == [600, 600]
    assert cfg.recent_dirs == []


def test_invalid_toml_returns_defaults(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text("not = valid = toml !!!\n", encoding="utf-8")
    assert load_config(p) == Config()


def test_splitter_sizes_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(splitter_sizes=[400, 800]), p)
    assert load_config(p).splitter_sizes == [400, 800]


def test_recent_dirs_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(recent_dirs=["/home/user", "/tmp"]), p)
    assert load_config(p).recent_dirs == ["/home/user", "/tmp"]


def test_unknown_keys_ignored(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('theme = "dark"\nfuture_key = "ignored"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.theme == "dark"
    assert not hasattr(cfg, "future_key")


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    p = tmp_path / "nested" / "deep" / "cfg.toml"
    save_config(Config(), p)
    assert p.exists()


def test_new_config_defaults() -> None:
    cfg = Config()
    assert cfg.sync_browsing is False
    assert cfg.file_type_colors is True
    assert cfg.show_hidden is False


def test_config_roundtrip_new_fields(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(sync_browsing=True, file_type_colors=False, show_hidden=True), p)
    cfg = load_config(p)
    assert cfg.sync_browsing is True
    assert cfg.file_type_colors is False
    assert cfg.show_hidden is True


def test_ai_api_key_migrated_to_claude_key(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('ai_api_key = "sk-old"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.ai_claude_key == "sk-old"


def test_ai_api_key_not_overwrite_existing_claude_key(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('ai_api_key = "sk-old"\nai_claude_key = "sk-new"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.ai_claude_key == "sk-new"


def test_config_ai_fields_have_defaults() -> None:
    cfg = Config()
    assert cfg.ai_default_provider == "claude"
    assert cfg.ai_claude_model == "claude-sonnet-4-20250514"
    assert cfg.ai_openai_model == "gpt-4o"
    assert cfg.ai_ollama_url == "http://localhost:11434"
    assert cfg.ai_ollama_model == "llama3.2"


def test_config_round_trip_ai_fields(tmp_path: Path) -> None:
    cfg = Config(ai_claude_key="sk-test", ai_openai_key="sk-oai", ai_ollama_model="mistral")
    save_config(cfg, tmp_path / "config.toml")
    loaded = load_config(tmp_path / "config.toml")
    assert loaded.ai_claude_key == "sk-test"
    assert loaded.ai_openai_key == "sk-oai"
    assert loaded.ai_ollama_model == "mistral"


def test_highlight_rules_types_roundtrip(tmp_path: Path) -> None:
    rule = {"enabled": True, "priority": 2, "color": "#ff0000", "pattern": "*.py"}
    cfg = Config(highlight_rules=[rule])
    p = tmp_path / "cfg.toml"
    save_config(cfg, p)
    loaded = load_config(p)
    r = loaded.highlight_rules[0]
    assert r["enabled"] is True
    assert r["priority"] == 2
    assert r["color"] == "#ff0000"


def test_layout_profiles_roundtrip(tmp_path: Path) -> None:
    profiles = {
        "my profile": {"left": "/home", "right": "/tmp", "split": 400},
        "work": {"left": "/work", "right": "/work/out", "split": 600},
    }
    cfg = Config(layout_profiles=profiles)
    p = tmp_path / "cfg.toml"
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.layout_profiles == profiles


def test_highlight_rules_multiple_dicts(tmp_path: Path) -> None:
    rules = [
        {"enabled": True, "priority": 1, "color": "#f00"},
        {"enabled": False, "priority": 5, "color": "#0f0"},
    ]
    cfg = Config(highlight_rules=rules)
    p = tmp_path / "cfg.toml"
    save_config(cfg, p)
    assert load_config(p).highlight_rules == rules


def test_save_config_no_tmp_file_left(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(), p)
    assert not p.with_suffix(".toml.tmp").exists()


def test_save_config_overwrites_stale_tmp(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.with_suffix(".toml.tmp").write_text("stale", encoding="utf-8")
    save_config(Config(), p)
    assert load_config(p) == Config()


def test_save_config_target_untouched_on_failure(tmp_path: Path, monkeypatch) -> None:
    import pytest
    p = tmp_path / "cfg.toml"
    save_config(Config(theme="light"), p)

    def boom(path, content, encoding="utf-8"):
        raise OSError("simulated crash")

    monkeypatch.setattr("biome_fm.config.atomic_write", boom)
    with pytest.raises(OSError):
        save_config(Config(theme="dark"), p)

    assert load_config(p).theme == "light"
