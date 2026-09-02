"""Tests for #23: API key migration from plaintext config to keyring."""
from __future__ import annotations

import tomllib
from pathlib import Path
from unittest.mock import patch


from biome_fm.config import Config, migrate_keys_to_keyring, save_config
from biome_fm.models import credential_store as cs


def test_migrate_moves_key_to_keyring(tmp_path: Path) -> None:
    """With no real keyring (fallback only), plaintext is copied to FALLBACK but NOT cleared."""
    cfg = Config(ai_claude_key="sk-test-123", ai_openai_key="")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)

    stored: dict = {}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            result = migrate_keys_to_keyring(cfg, config_path)

    # Fallback returns False from set_credential → plaintext is kept
    assert result.ai_claude_key == "sk-test-123"
    assert stored.get(("biome-fm", "claude")) == "sk-test-123"
    saved = tomllib.loads(config_path.read_text())
    # Config not rewritten (nothing was durably stored)
    assert saved.get("ai_claude_key", "") == "sk-test-123"


def test_migrate_does_not_overwrite_existing_keyring(tmp_path: Path) -> None:
    cfg = Config(ai_claude_key="sk-new")
    stored: dict = {("biome-fm", "claude"): "sk-existing"}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            migrate_keys_to_keyring(cfg, tmp_path / "cfg.toml")

    assert stored[("biome-fm", "claude")] == "sk-existing"


def test_migrate_both_keys(tmp_path: Path) -> None:
    """With no real keyring, both keys are copied to FALLBACK but NOT cleared."""
    cfg = Config(ai_claude_key="claude-key", ai_openai_key="openai-key")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)

    stored: dict = {}
    with patch.object(cs, "_keyring", None):
        with patch.object(cs, "_FALLBACK", stored):
            result = migrate_keys_to_keyring(cfg, config_path)

    # Fallback returns False → keys are kept in config
    assert result.ai_claude_key == "claude-key"
    assert result.ai_openai_key == "openai-key"
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


def test_migrate_keeps_plaintext_when_no_keyring(tmp_path: Path) -> None:
    """Plaintext key must survive in config when keyring unavailable (set_credential returns False)."""
    cfg = Config(ai_claude_key="sk-test")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)
    with patch.object(cs, "_keyring", None):
        migrate_keys_to_keyring(cfg, config_path)
    from biome_fm.config import load_config
    assert load_config(config_path).ai_claude_key == "sk-test"


def test_migrate_clears_plaintext_with_real_keyring(tmp_path: Path) -> None:
    """With a working keyring backend, plaintext IS cleared from config."""
    from unittest.mock import MagicMock
    cfg = Config(ai_claude_key="sk-real")
    config_path = tmp_path / "config.toml"
    save_config(cfg, config_path)
    mock_kr = MagicMock()
    mock_kr.set_password.return_value = None
    mock_kr.get_password.return_value = None  # nothing stored yet
    with patch.object(cs, "_keyring", mock_kr):
        result = migrate_keys_to_keyring(cfg, config_path)
    assert result.ai_claude_key == ""
    from biome_fm.config import load_config
    assert load_config(config_path).ai_claude_key == ""


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
