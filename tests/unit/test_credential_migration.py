"""Tests for #23: API key migration from plaintext config to keyring."""
from __future__ import annotations

import tomllib
from pathlib import Path
from unittest.mock import patch


from biome_fm.config import Config, migrate_keys_to_keyring, save_config
from biome_fm.models import credential_store as cs


def test_migrate_moves_key_to_keyring(tmp_path: Path) -> None:
    cfg = Config(ai_claude_key="sk-test-123", ai_openai_key="")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)

    stored: dict = {}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            result = migrate_keys_to_keyring(cfg, config_path)

    assert result.ai_claude_key == ""
    assert stored.get(("biome-fm", "claude")) == "sk-test-123"
    saved = tomllib.loads(config_path.read_text())
    assert saved.get("ai_claude_key", "") == ""


def test_migrate_does_not_overwrite_existing_keyring(tmp_path: Path) -> None:
    cfg = Config(ai_claude_key="sk-new")
    stored: dict = {("biome-fm", "claude"): "sk-existing"}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            migrate_keys_to_keyring(cfg, tmp_path / "cfg.toml")

    assert stored[("biome-fm", "claude")] == "sk-existing"


def test_migrate_both_keys(tmp_path: Path) -> None:
    cfg = Config(ai_claude_key="claude-key", ai_openai_key="openai-key")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)

    stored: dict = {}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            result = migrate_keys_to_keyring(cfg, config_path)

    assert result.ai_claude_key == ""
    assert result.ai_openai_key == ""
    assert stored[("biome-fm", "claude")] == "claude-key"
    assert stored[("biome-fm", "openai")] == "openai-key"


def test_migrate_no_op_when_no_plaintext_keys(tmp_path: Path) -> None:
    """If config has no plaintext keys, nothing is written to keyring."""
    cfg = Config(ai_claude_key="", ai_openai_key="")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)

    stored: dict = {}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            migrate_keys_to_keyring(cfg, config_path)

    assert stored == {}


def test_make_providers_reads_from_credential_store() -> None:
    """make_providers uses keyring key even when config fields are empty."""
    cfg = Config(ai_claude_key="", ai_openai_key="")
    stored: dict = {("biome-fm", "claude"): "sk-from-keyring"}

    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            with patch("biome_fm.ai.claude_provider.ClaudeProvider") as MockClaude:
                from biome_fm.ai.provider import make_providers
                make_providers(cfg)

    MockClaude.assert_called_once()
    assert MockClaude.call_args[0][0] == "sk-from-keyring"
