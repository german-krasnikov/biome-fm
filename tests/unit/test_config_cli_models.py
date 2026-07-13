from biome_fm.config import Config, load_config, save_config


def test_config_cli_model_defaults():
    cfg = Config()
    assert cfg.ai_cli_claude_code_model == ""
    assert cfg.ai_cli_codex_model == ""
    assert cfg.ai_cli_opencode_model == ""


def test_config_cli_model_roundtrip(tmp_path):
    cfg = Config(ai_cli_claude_code_model="claude-opus-4-6-20250804")
    p = tmp_path / "cfg.toml"
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.ai_cli_claude_code_model == "claude-opus-4-6-20250804"


def test_standard_provider_model_fields_exist():
    """Verify Config has fields for standard (non-CLI) providers."""
    cfg = Config()
    assert hasattr(cfg, "ai_claude_model")
    assert hasattr(cfg, "ai_openai_model")
    assert hasattr(cfg, "ai_ollama_model")
