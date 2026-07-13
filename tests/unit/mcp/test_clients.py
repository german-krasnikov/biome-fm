"""Tests for mcp.clients registry and detection."""


from biome_fm.mcp.clients import CLIENT_REGISTRY, ClientInfo, detect_installed


def test_client_registry_has_claude_code():
    assert "claude-code" in CLIENT_REGISTRY
    assert CLIENT_REGISTRY["claude-code"].root_key == "mcpServers"


def test_client_registry_has_expected_clients():
    expected = {"claude-code", "claude-desktop", "cursor", "windsurf", "vscode", "codex", "kimi"}
    assert expected.issubset(set(CLIENT_REGISTRY.keys()))


def test_detect_installed_returns_when_config_exists(tmp_path, monkeypatch):
    import biome_fm.mcp.clients as mod

    cfg = tmp_path / "test.json"
    cfg.write_text("{}")  # config file exists → client is installed
    fake_client = ClientInfo(
        name="Test",
        config_path=cfg,
        scope="user",
        root_key="mcpServers",
    )
    monkeypatch.setattr(mod, "CLIENT_REGISTRY", {"test-client": fake_client})
    result = detect_installed()
    assert result == ["test-client"]


def test_detect_installed_returns_when_binary_found(tmp_path, monkeypatch):
    import shutil

    import biome_fm.mcp.clients as mod

    fake_client = ClientInfo(
        name="Test",
        config_path=tmp_path / "test.json",  # config absent
        scope="user",
        root_key="mcpServers",
        binary="python",  # python is always on PATH
    )
    monkeypatch.setattr(mod, "CLIENT_REGISTRY", {"test-client": fake_client})
    result = detect_installed()
    assert ("test-client" in result) == bool(shutil.which("python"))


def test_detect_installed_excludes_missing(tmp_path, monkeypatch):
    import biome_fm.mcp.clients as mod

    fake_client = ClientInfo(
        name="Missing",
        config_path=tmp_path / "nonexistent_dir" / "test.json",
        scope="user",
        root_key="mcpServers",
        binary="__biome_fm_nonexistent_binary__",
    )
    monkeypatch.setattr(mod, "CLIENT_REGISTRY", {"missing": fake_client})
    assert detect_installed() == []
