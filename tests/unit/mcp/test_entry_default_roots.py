"""Test that mcp._entry.main() defaults allowed_roots to [Path.home()]."""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _fake_server_module(calls: list) -> types.ModuleType:
    fake = MagicMock()
    fake.run.return_value = None

    mod = types.ModuleType("biome_fm.mcp.server")

    def create_server(roots):
        calls.append(roots)
        return fake

    mod.create_server = create_server  # type: ignore[attr-defined]
    return mod


def test_mcp_main_default_restricts_to_home(monkeypatch):
    calls: list[list[Path]] = []
    monkeypatch.setitem(sys.modules, "biome_fm.mcp.server", _fake_server_module(calls))

    from biome_fm.mcp._entry import main
    main()
    assert calls == [[Path.home()]]


def test_mcp_main_explicit_roots_passed_through(monkeypatch, tmp_path):
    calls: list[list[Path]] = []
    monkeypatch.setitem(sys.modules, "biome_fm.mcp.server", _fake_server_module(calls))

    from biome_fm.mcp._entry import main
    main(allowed_roots=[tmp_path])
    assert calls == [[tmp_path]]
