"""Tests for mcp.cli dispatch routing."""

import biome_fm.mcp.clients as clients_mod
import biome_fm.mcp.merger as merger_mod
import biome_fm.mcp.resolver as resolver_mod
from biome_fm.mcp.cli import UNHANDLED, dispatch
from biome_fm.mcp.clients import ClientInfo


def test_dispatch_unknown_returns_unhandled():
    assert dispatch(["foobar"]) is UNHANDLED


def test_dispatch_empty_returns_unhandled():
    assert dispatch([]) is UNHANDLED


def test_dispatch_version_returns_zero(capsys):
    result = dispatch(["version"])
    assert result == 0
    out = capsys.readouterr().out
    assert "0." in out  # some semver output


def test_configure_calls_merger(monkeypatch, tmp_path):
    fake_client = ClientInfo(
        name="Test",
        config_path=tmp_path / "mcp.json",
        scope="user",
        root_key="mcpServers",
    )
    monkeypatch.setattr(clients_mod, "CLIENT_REGISTRY", {"test": fake_client})
    monkeypatch.setattr(clients_mod, "detect_installed", lambda: ["test"])
    monkeypatch.setattr(resolver_mod, "find_server_command", lambda: ["uvx", "biome-fm-mcp"])

    calls = []
    monkeypatch.setattr(merger_mod, "merge_mcp_config", lambda c, e: calls.append(c))

    result = dispatch(["configure"])
    assert result == 0
    assert len(calls) == 1
    assert calls[0].name == "Test"


def test_configure_with_explicit_client(monkeypatch, tmp_path):
    fake_client = ClientInfo(
        name="Cursor",
        config_path=tmp_path / "mcp.json",
        scope="user",
        root_key="mcpServers",
    )
    monkeypatch.setattr(clients_mod, "CLIENT_REGISTRY", {"cursor": fake_client})
    monkeypatch.setattr(resolver_mod, "find_server_command", lambda: ["uvx", "biome-fm-mcp"])

    calls = []
    monkeypatch.setattr(merger_mod, "merge_mcp_config", lambda c, e: calls.append(c))

    result = dispatch(["configure", "--client=cursor"])
    assert result == 0
    assert len(calls) == 1


def test_configure_unknown_client_returns_error(monkeypatch):
    monkeypatch.setattr(clients_mod, "CLIENT_REGISTRY", {})
    result = dispatch(["configure", "--client=nonexistent"])
    assert result == 1


def test_configure_no_clients_detected(monkeypatch):
    monkeypatch.setattr(clients_mod, "detect_installed", lambda: [])
    result = dispatch(["configure"])
    assert result == 1


def test_doctor_reports_status(tmp_path, monkeypatch, capsys):
    import json

    from biome_fm.mcp.clients import SERVER_NAME

    cfg = tmp_path / "mcp.json"
    cfg.write_text(json.dumps({"mcpServers": {SERVER_NAME: {"command": "uvx"}}}))

    fake_client = ClientInfo(
        name="Test",
        config_path=cfg,
        scope="user",
        root_key="mcpServers",
    )
    monkeypatch.setattr(clients_mod, "CLIENT_REGISTRY", {"test": fake_client})

    result = dispatch(["doctor"])
    assert result == 0
    assert "[OK]" in capsys.readouterr().out


def test_uninstall_removes_entries(monkeypatch, tmp_path):
    fake_client = ClientInfo(
        name="Test",
        config_path=tmp_path / "mcp.json",
        scope="user",
        root_key="mcpServers",
    )
    monkeypatch.setattr(clients_mod, "CLIENT_REGISTRY", {"test": fake_client})

    removed = []
    monkeypatch.setattr(merger_mod, "remove_mcp_entry", lambda c: removed.append(c) or True)

    result = dispatch(["uninstall"])
    assert result == 0
    assert len(removed) == 1
