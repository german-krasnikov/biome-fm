"""Tests for mcp.resolver command detection."""

import biome_fm.mcp.resolver as mod
from biome_fm.mcp.resolver import build_server_entry, find_server_command


def test_prefers_uvx(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/uvx" if x == "uvx" else None)
    cmd = find_server_command()
    assert cmd == ["/usr/local/bin/uvx", "biome-fm-mcp"]


def test_falls_back_to_python(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda x: None)
    # Point executable to tmp_path so venv-bin check fails (no biome-fm-mcp there)
    fake_exe = str(tmp_path / "bin" / "python3")
    FakeSys = type("FakeSys", (), {"executable": fake_exe})
    monkeypatch.setattr(mod, "sys", FakeSys())
    cmd = find_server_command()
    assert cmd == [fake_exe, "-m", "biome_fm.mcp._entry"]


def test_prefers_venv_bin_over_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda x: None)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "biome-fm-mcp").touch()
    fake_exe = str(bin_dir / "python3")
    FakeSys = type("FakeSys", (), {"executable": fake_exe})
    monkeypatch.setattr(mod, "sys", FakeSys())
    cmd = find_server_command()
    assert cmd == [str(bin_dir / "biome-fm-mcp")]


def test_build_server_entry_format():
    entry = build_server_entry(["uvx", "biome-fm-mcp"])
    assert entry == {"command": "uvx", "args": ["biome-fm-mcp"]}


def test_build_server_entry_no_args():
    entry = build_server_entry(["/usr/bin/biome-fm-mcp"])
    assert entry == {"command": "/usr/bin/biome-fm-mcp", "args": []}


def test_build_server_entry_uses_find_when_none(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/uvx" if x == "uvx" else None)
    entry = build_server_entry()
    assert entry["command"] == "/usr/bin/uvx"
    assert entry["args"] == ["biome-fm-mcp"]
