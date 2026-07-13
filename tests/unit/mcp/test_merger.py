"""Tests for mcp.merger JSON/TOML patching."""

import json

from biome_fm.mcp.clients import ClientInfo, SERVER_NAME
from biome_fm.mcp.merger import (
    merge_mcp_config,
    merge_toml_mcp,
    remove_mcp_entry,
    remove_toml_mcp_entry,
)


def _client(tmp_path, filename="config.json"):
    return ClientInfo(
        name="Test",
        config_path=tmp_path / filename,
        scope="user",
        root_key="mcpServers",
    )


# --- JSON ---

def test_merge_creates_new_config(tmp_path):
    client = _client(tmp_path)
    entry = {"command": "uvx", "args": ["biome-fm-mcp"]}
    merge_mcp_config(client, entry)
    data = json.loads((tmp_path / "config.json").read_text())
    assert data["mcpServers"][SERVER_NAME] == entry


def test_merge_preserves_existing_entries(tmp_path):
    client = _client(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"mcpServers": {"other": {"command": "other"}}})
    )
    merge_mcp_config(client, {"command": "uvx", "args": []})
    data = json.loads((tmp_path / "config.json").read_text())
    assert "other" in data["mcpServers"]
    assert SERVER_NAME in data["mcpServers"]


def test_merge_overwrites_own_entry(tmp_path):
    client = _client(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"mcpServers": {SERVER_NAME: {"command": "old"}}})
    )
    merge_mcp_config(client, {"command": "new"})
    data = json.loads((tmp_path / "config.json").read_text())
    assert data["mcpServers"][SERVER_NAME]["command"] == "new"


def test_merge_applies_entry_transformer(tmp_path):
    client = ClientInfo(
        name="VSCode",
        config_path=tmp_path / "settings.json",
        scope="user",
        root_key="servers",
        entry_transformer=lambda e: {**e, "type": "stdio"},
    )
    merge_mcp_config(client, {"command": "uvx", "args": []})
    data = json.loads((tmp_path / "settings.json").read_text())
    assert data["servers"][SERVER_NAME]["type"] == "stdio"


def test_remove_entry_returns_false_when_absent(tmp_path):
    client = _client(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"mcpServers": {}}))
    assert remove_mcp_entry(client) is False


def test_remove_entry_removes_and_returns_true(tmp_path):
    client = _client(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"mcpServers": {SERVER_NAME: {"command": "x"}}})
    )
    assert remove_mcp_entry(client) is True
    data = json.loads((tmp_path / "config.json").read_text())
    assert SERVER_NAME not in data["mcpServers"]


def test_remove_returns_false_when_file_missing(tmp_path):
    client = _client(tmp_path)
    assert remove_mcp_entry(client) is False


# --- TOML ---

def test_merge_toml_creates_section(tmp_path):
    path = tmp_path / "config.toml"
    merge_toml_mcp(path, {"command": "uvx", "args": ["biome-fm-mcp"]})
    content = path.read_text()
    assert SERVER_NAME in content
    assert "command" in content


def test_remove_toml_entry(tmp_path):
    path = tmp_path / "config.toml"
    merge_toml_mcp(path, {"command": "uvx", "args": ["biome-fm-mcp"]})
    assert remove_toml_mcp_entry(path) is True
    content = path.read_text()
    assert SERVER_NAME not in content


def test_remove_toml_returns_false_when_absent(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[other]\nkey = 1\n")
    assert remove_toml_mcp_entry(path) is False


def test_remove_toml_returns_false_when_missing(tmp_path):
    path = tmp_path / "missing.toml"
    assert remove_toml_mcp_entry(path) is False
